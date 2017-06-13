# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.model import ModelSQL, ModelView, fields
from trytond.pyson import Eval
from trytond.transaction import Transaction
from trytond.pool import Pool, PoolMeta
from trytond.model import ModelSQL, ModelView, fields

__all__ = ['Invoice']


class Invoice:
    __metaclass__ = PoolMeta
    __name__ = 'account.invoice'
    shipment_addresses = fields.Function(fields.Many2Many('party.address',
        None, None, 'Shipment Addresses'), 'get_shipment_addresses')
    shipment_address = fields.Function(fields.Many2One('party.address',
        'Shipment Address'), 'get_shipment_address')

    def get_shipment_addresses(self, name=None):
        addresses = set()
        for line in self.lines:
            if line.origin and line.origin.__name__ == 'sale.line':
                if line.origin.sale and line.origin.sale.invoice_address:
                    addresses.add(line.origin.sale.shipment_address)
        return [address.id for address in addresses]

    def get_shipment_address(self, name=None):
        if self.shipment_addresses:
            return self.shipment_addresses[0].id
