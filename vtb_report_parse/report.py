# -*- coding: utf-8 -*-
import enum
from datetime import datetime
import logging
import os
import re
import collections

from lxml import etree

LOG = logging.getLogger(__name__)


class ParseError(Exception):
    pass


class ElementNotFound(ParseError):
    def __init__(self, element):
        msg = 'Cannot find %r tag' % element
        super(ElementNotFound, self).__init__(msg)


class ElementWithAttrNotFound(ParseError):
    def __init__(self, attribute):
        msg = 'Cannot find element with %r attr' % attribute
        super(ElementWithAttrNotFound, self).__init__(msg)


Operation = collections.namedtuple(
    'Operation',
    ('value', 'currency', 'date', 'operation_type', 'comment')
)


@enum.unique
class OperationType(enum.Enum):
    fees = 'Вознаграждение Брокера'
    exhange_saldo = 'Сальдо расчётов по сделкам с иностранной валютой'
    securities_saldo = 'Сальдо расчётов по сделкам с ценными бумагами'
    credit_payments = 'Зачисление денежных средств'
    close_out = 'Погашение ценных бумаг'
    dividends = 'Дивиденды'
    coupons = 'Купонный доход'
    taxes = 'НДФЛ'
    write_offs = 'Списание денежных средств'
    unknown = 'unknown'


class CashFlow(object):
    def __init__(self):
        self._values = []

    def add(self, operation):
        self._values.append(operation)

    def merge(self, other, union=False):
        if union:
            for val in other:
                self.add(val)
        else:
            self_op_by_date = collections.defaultdict(list)
            other_op_by_date = collections.defaultdict(list)
            for val in self:
                self_op_by_date[val.date].append(val)
            for val in other:
                other_op_by_date[val.date].append(val)

            new_dates = set(other_op_by_date.keys()) - set(self_op_by_date.keys())
            for date in new_dates:
                for val in other_op_by_date[date]:
                    self.add(val)

    def filter_by_type(self, operation_types):
        if not isinstance(operation_types, (list, tuple)):
            operation_types = [operation_types]
        result = []
        for value in self._values:
            if value.operation_type in operation_types:
                result.append(value)

        result = sorted(result, key=lambda val: val.date)
        return result

    def __iter__(self):
        values = sorted(self._values, key=lambda val: val.date)
        return iter(values)


class VTBReportParser(object):
    def __init__(self, report_file):
        if not os.path.exists(report_file):
            raise ParseError('File %r is not found' % report_file)
        with open(report_file) as fd:
            self._root = etree.XML(fd.read())

        self._report_date = None
        self._usd_price = None
        self._cash_flow = None
        self._client_code = None

    @property
    def report_date(self):
        if self._report_date is None:
            el = self._root.find('.//{*}TablixTitul')
            if el is None:
                raise ElementNotFound('TablixTitul')

            text = None
            for attr in el.attrib:
                if attr.startswith('Textbox'):
                    text = el.attrib[attr].encode('utf-8')
                    break
            else:
                raise ElementNotFound('Textbox')
            m = re.search(r'(\d+\.\d+\.\d+) .* (\d+\.\d+\.\d+)', text)
            if not m:
                LOG.error('Text: %s', text)
                raise ParseError('Cannot parse TablixTitul[@Textbox] value')
            groups = m.groups()
            sdate = datetime.strptime(groups[0], '%d.%m.%Y')
            edate = datetime.strptime(groups[1], '%d.%m.%Y')
            self._report_date = sdate, edate

        return self._report_date

    @property
    def usd_price(self):
        if self._usd_price is None:
            item = self._root.find('.//*/[@CurrEnd]')
            if item is None:
                LOG.warning("Cannot find element with 'CurrEnd' attr.")
                self._usd_price = 0
            else:
                self._usd_price = float(item.attrib['CurrEnd'])

        return self._usd_price

    @property
    def cash_flow(self):
        if self._cash_flow is None:
            self._cash_flow = CashFlow()

            dds_place = self._root.find('.//{*}DDS_place')
            if dds_place is None:
                raise ElementNotFound('DDS_place')

            dds_items = dds_place.findall('.//*/[@debt_date4]')
            dds_items = dds_items or []
            if dds_items:
                expected_keys = ('debt_date4', 'debt_type4', 'decree_amount2',
                                 'notes1', 'operation_type')
                attr_names = dds_items[0].attrib.keys()
                missed_keys = set(attr_names) - set(expected_keys)
                if missed_keys:
                    msg = ('Cannot find cash flow attributes: %s', ', '
                           .join(missed_keys))
                    raise ParseError(msg)

            for dds_item in dds_items:
                item = {'comment': None}
                for attr, value in dds_item.attrib.items():
                    if attr == 'debt_date4':
                        item['value'] = float(value)
                    elif attr == 'decree_amount2':
                        item['currency'] = value
                    elif attr == 'debt_type4':
                        item['date'] = (
                            datetime.strptime(value, '%Y-%m-%dT%S:%M:%H'))
                    elif attr == 'operation_type':
                        value = value.encode('utf-8')
                        if value not in OperationType._value2member_map_:
                            LOG.warning('Unknown operation type: %s', value)
                            enum_value = OperationType('unknown')
                        else:
                            enum_value = OperationType(value)
                        item['operation_type'] = enum_value
                    elif attr == 'notes1':
                        item['comment'] = value
                    else:
                        LOG.warning('Unknown attrib name: %s', attr)
                self._cash_flow.add(Operation(**item))

        return self._cash_flow

    @property
    def client_code(self):
        if not self._client_code:
            item = self._root.find('.//*/[@client_code1]')
            if item is None:
                raise ElementWithAttrNotFound('client_code1')
            self._client_code = item.attrib['client_code1']
        return self._client_code


class VTBReport(object):
    def __init__(self, report_files):
        parsers = []
        for report_file in report_files:
            parser = VTBReportParser(report_file)
            parsers.append(parser)

        self._sdate = None
        self._edate = None
        self._cash_flow = CashFlow()
        client_code = parsers[0].client_code
        for parser in parsers:
            if not self._sdate or self._sdate > parser.report_date[0]:
                self._sdate = parser.report_date[0]
            if not self._edate or self._edate < parser.report_date[1]:
                self._edate = parser.report_date[1]
                if parser.usd_price:
                    self._usd_price = parser.usd_price

            union = parser.client_code != parsers[0].client_code
            self._cash_flow.merge(parser.cash_flow, union=union)

    @property
    def report_date(self):
        return self._sdate, self._edate

    @property
    def usd_price(self):
        return self._usd_price

    @property
    def cash_flow(self):
        return self._cash_flow
