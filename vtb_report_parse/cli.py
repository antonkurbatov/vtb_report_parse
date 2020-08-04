# -*- coding: utf-8 -*-
import argparse
import logging

from vtb_report_parse import report as vtb_report

OperationType = vtb_report.OperationType
LOG = logging.getLogger()


def dump_cash_flow(report, tag, operation_types=None):
    rur = 0
    usd = 0
    if operation_types:
        result = report.cash_flow.filter_by_type(operation_types)
    else:
        result = report.cash_flow

    for item in result:
        if item.currency == 'RUR':
            rur += item.value
        elif item.currency == 'USD':
            usd += item.value
        else:
            raise Exception('Unknown currency: %s' % item.currency)
    LOG.info('[%s] %s₽, %s$ (%s₽)',
             tag, rur, usd, round(rur + usd * report.usd_price, 2))


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--verbose', '-v',
                        action='count',
                        help='verbose logging')
    parser.add_argument('--report',
                        metavar='<report-file.xml>',
                        dest='reports',
                        action='append',
                        required=True,
                        help='A VTB broker report file.This option can be '
                             'used multiple times to merge reports together.')
    parser.add_argument('--usd-price',
                        metavar='<usd-price>',
                        type=float,
                        help='USD value in ₽. If not specified the '
                             'value is gotten form the report.')
    return parser.parse_args()


def main():
    parsed_args = parse_args()

    logging_map = {
        0: logging.WARNING,
        1: logging.INFO,
        2: logging.DEBUG,
    }

    LOG.setLevel(logging_map.get(parsed_args.verbose, logging.DEBUG))
    logging.basicConfig(format='%(message)s')

    LOG.info('Processing the report(s):\n- %s', '\n- '.join(parsed_args.reports))
    report = vtb_report.VTBReport(parsed_args.reports)

    start_date, end_date = report.report_date
    usd_price = parsed_args.usd_price or report.usd_price
    LOG.info('[Period] %s - %s (%s days)',
             start_date.date(), end_date.date(),
             (end_date - start_date).days)

    usd_price = parsed_args.usd_price or report.usd_price
    LOG.info("[USD price] %s", usd_price)

    def output_dump(tag, operation_types=None):
        dump_cash_flow(report, tag, operation_types)

    LOG.info('---- Cash Flow ----')
    output_dump('Fees', OperationType.fees)
    output_dump('Taxes', OperationType.taxes)
    output_dump('Dividends', OperationType.dividends)
    output_dump('Coupons', OperationType.coupons)
    output_dump('Credit payments', OperationType.credit_payments)
    output_dump('Write offs', OperationType.write_offs)
    output_dump('Exhange saldo', OperationType.exhange_saldo)
    output_dump('Securities saldo', OperationType.securities_saldo)

    LOG.info('---- Summary ----')
    output_dump('Credit payments with write offs',
                [OperationType.credit_payments, OperationType.write_offs])
    output_dump('Total')


if __name__ == '__main__':
    main()
