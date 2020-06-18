# -*- coding: utf-8 -*-
import enum
from datetime import datetime
import logging
import os
import re
import collections

from lxml import etree

LOG = logging.getLogger()


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

    def filter_by_type(self, operation_types):
        if not isinstance(operation_types, (list, tuple)):
            operation_types = [operation_types]
        result = []
        for value in self._values:
            if value.operation_type in operation_types:
                result.append(value)
        return result

    def __iter__(self):
        return iter(self._values)


class VTBReport(object):
    def __init__(self, report_file):
        self._parse_init(report_file)

    def _parse_init(self, report_file):
        if not os.path.exists(report_file):
            raise ParseError('File %r is not found' % report_file)
        with open(report_file) as fd:
            self._root = etree.XML(fd.read())

        self._start_date, self._end_date = self._parse_date()
        self._usd_price = self._parse_end_usd()
        self._cash_flow = self._parse_cash_flow()

    def _parse_date(self):
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
        return sdate, edate

    def _parse_end_usd(self):
        item = self._root.find('.//*/[@CurrEnd]')
        if item is None:
            LOG.warning("Cannot find element with 'CurrEnd' attr. "
                        "USD price will be set to 0.")
            return 0
        return float(item.attrib['CurrEnd'])

    def _parse_cash_flow(self):
        cash_flow = CashFlow()

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
            cash_flow.add(Operation(**item))

        return cash_flow

    @property
    def report_date(self):
        return self._start_date, self._end_date

    @property
    def usd_price(self):
        return self._usd_price

    @property
    def cash_flow(self):
        return self._cash_flow
