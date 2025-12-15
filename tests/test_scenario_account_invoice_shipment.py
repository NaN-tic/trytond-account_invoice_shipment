import unittest
from decimal import Decimal

from proteus import Model
from trytond.modules.account.tests.tools import (create_chart,
                                                 create_fiscalyear, create_tax,
                                                 get_accounts)
from trytond.modules.account_invoice.tests.tools import (
    create_payment_term, set_fiscalyear_invoice_sequences)
from trytond.modules.company.tests.tools import create_company, get_company
from trytond.tests.test_tryton import drop_db
from trytond.tests.tools import activate_modules
from datetime import date


class Test(unittest.TestCase):

    def setUp(self):
        drop_db()
        super().setUp()

    def tearDown(self):
        drop_db()
        super().tearDown()

    def test(self):

        # Install account_invoice_shipment Module
        config = activate_modules(['account_invoice_shipment', 'sale'])

        today = date.today()

        # Create company
        _ = create_company()
        company = get_company()

        # Reload the context
        User = Model.get('res.user')
        config._context = User.get_preferences(True, config.context)

        # Create fiscal year
        fiscalyear = set_fiscalyear_invoice_sequences(
            create_fiscalyear(company))
        fiscalyear.click('create_period')

        # Create chart of accounts
        _ = create_chart(company)
        accounts = get_accounts(company)
        revenue = accounts['revenue']
        expense = accounts['expense']

        # Create tax
        tax = create_tax(Decimal('.10'))
        tax.save()

        # Create parties
        Party = Model.get('party.party')
        customer = Party(name='Customer')
        customer.save()

        # Create account category
        ProductCategory = Model.get('product.category')
        account_category = ProductCategory(name="Account Category")
        account_category.accounting = True
        account_category.account_expense = expense
        account_category.account_revenue = revenue
        account_category.customer_taxes.append(tax)
        account_category.save()

        # Create product
        ProductUom = Model.get('product.uom')
        unit, = ProductUom.find([('name', '=', 'Unit')])
        ProductTemplate = Model.get('product.template')
        Product = Model.get('product.product')
        product = Product()
        template = ProductTemplate()
        template.name = 'product'
        template.default_uom = unit
        template.type = 'goods'
        template.salable = True
        template.list_price = Decimal('10')
        template.cost_price = Decimal('5')
        template.cost_price_method = 'fixed'
        template.account_category = account_category
        template.save()
        product.template = template
        product.save()

        # Create payment term
        payment_term = create_payment_term()
        payment_term.save()

        # Create sale
        Sale = Model.get('sale.sale')
        SaleLine = Model.get('sale.line')
        sale = Sale()
        sale.party = customer
        sale.payment_term = payment_term
        sale.invoice_method = 'order'
        sale_line = SaleLine()
        sale.lines.append(sale_line)
        sale_line.product = product
        sale_line.quantity = 2.0
        sale_line = SaleLine()
        sale.lines.append(sale_line)
        sale_line.product = product
        sale_line.quantity = 3.0
        sale.click('quote')
        sale.click('confirm')
        sale.click('process')
        invoice, = sale.invoices
        self.assertEqual(len(invoice.shipment_origin_addresses), 1)
        self.assertNotEqual(invoice.shipment_origin_address, None)
        line1, line2 = invoice.lines
        self.assertEqual(len(line1.shipments_origin), 1)
        shipment1, = line1.shipments_origin

        self.assertEqual(line1.shipments_origin_number, '1')
        self.assertEqual(line1.shipments_origin_effective_date, '')
        self.assertEqual(line1.shipment_addresses_name, 'Customer')

        # set effective date and check origin effective date format
        shipment1, = line1.shipments_origin
        shipment1.effective_date = today
        shipment1.save()
        line1.reload()
        self.assertEqual(line1.shipments_origin_effective_date, today.strftime('%m/%d/%Y'))
