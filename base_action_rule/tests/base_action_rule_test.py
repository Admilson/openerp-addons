from openerp import SUPERUSER_ID
from openerp.tests import common
from .. import test_models

class base_action_rule_test(common.TransactionCase):

    def setUp(self):
        """*****setUp*****"""
        super(base_action_rule_test, self).setUp()
        cr, uid = self.cr, self.uid
        self.demo = self.registry('ir.model.data').get_object(cr, uid, 'base', 'user_demo').id
        self.admin = SUPERUSER_ID
        self.model = self.registry('base.action.rule.lead.test')

    def create_filter_done(self, cr, uid, context=None):
        filter_pool = self.registry('ir.filters')
        return filter_pool.create(cr, uid, {
            'name': "Lead is in done state",
            'is_default': False,
            'model_id': 'base.action.rule.lead.test',
            'domain' : "[('state','=','done')]",
            }, context=context)

    def create_filter_draft(self, cr, uid, context=None):
        filter_pool = self.registry('ir.filters')
        return filter_pool.create(cr, uid, {
            'name': "Lead is in draft state",
            'is_default': False,
            'model_id': "base.action.rule.lead.test",
            'domain' : "[('state','=','draft')]",
            }, context=context)

    def create_lead_test_1(self, cr, uid, context=None):
        """
            Create a new lead_test
        """
        return self.model.create(cr, uid, {
            'name': "Lead Test 1",
            'user_id': self.admin,
            }, context=context)

    def create_rule(self, cr, uid, filter_id=False, filter_pre_id=False, context=None):
        """
            The "Rule 1" says that when a lead goes to the 'draft' state, the responsible for that lead changes to user "demo"
        """
        self.action_pool = self.registry('base.action.rule')
        return self.action_pool.create(cr,uid,{
            'name' : "Rule 1",
            'model_id': self.registry('ir.model').search(cr, uid, [('model','=','base.action.rule.lead.test')], context=context)[0],
            'active' : 1,
            'trg_date_type' : 'none',
            'filter_pre_id' : filter_pre_id,
            'filter_id' : filter_id,
            'act_user_id': self.demo,
            }, context=context)

    def test_00_check_to_state_draft_pre(self):
        """
        Check that a new record (with state = draft) doesn't change its responsible when there is a precondition filter which check that the state is draft.
        """
        cr, uid = self.cr, self.uid
        filter_draft = self.create_filter_draft(cr, uid)
        rule_1_id = self.create_rule(cr, uid, filter_pre_id=filter_draft)
        new_lead_id = self.create_lead_test_1(cr, uid)
        new_lead = self.model.browse(cr, uid, new_lead_id)
        self.assertEquals(new_lead.state, 'draft')
        self.assertEquals(new_lead.user_id.id, self.admin)

    def test_01_check_to_state_draft_post(self):
        """
        Check that a new record (with state = draft) changes its responsible when there is a postcondition filter which check that the state is draft.
        """
        cr, uid = self.cr, self.uid
        filter_draft = self.create_filter_draft(cr, uid)
        rule_1_id = self.create_rule(cr, uid, filter_id=filter_draft)
        new_lead_id = self.create_lead_test_1(cr, uid)
        new_lead = self.model.browse(cr, uid, new_lead_id)
        self.assertEquals(new_lead.state, 'draft')
        self.assertEquals(new_lead.user_id.id, self.demo)

    def test_02_check_from_draft_to_done_with_steps(self):
        """
        A new record will be created and will goes from draft to done state via the other states (open, pending and cancel)
        We will create a rule that says in precondition that the record must be in the "draft" state while a postcondition filter says
        that the record will be done. If the state goes from 'draft' to 'done' the responsible will change. If those two conditions aren't
        verified, the responsible will stay the same
        The responsible in that test will never change
        """
        cr, uid = self.cr, self.uid
        filter_draft = self.create_filter_draft(cr, uid)
        filter_done = self.create_filter_done(cr, uid)
        self.create_rule(cr, uid, filter_pre_id=filter_draft, filter_id=filter_done)
        new_lead_id = self.create_lead_test_1(cr, uid)
        new_lead = self.model.browse(cr, uid, new_lead_id)
        self.assertEquals(new_lead.state, 'draft')
        self.assertEquals(new_lead.user_id.id, self.admin)
        """ change the state of new_lead to open and check that responsible doen't change"""
        new_lead.write({'state': 'open'})
        new_lead = self.model.browse(cr, uid, new_lead_id)
        self.assertEquals(new_lead.state, 'open')
        self.assertEquals(new_lead.user_id.id, self.admin)
        """ change the state of new_lead to pending and check that responsible doen't change"""
        new_lead.write({'state': 'pending'})
        new_lead = self.model.browse(cr, uid, new_lead_id)
        self.assertEquals(new_lead.state, 'pending')
        self.assertEquals(new_lead.user_id.id, self.admin)
        """ change the state of new_lead to cancel and check that responsible doen't change"""
        new_lead.write({'state': 'cancel'})
        new_lead = self.model.browse(cr, uid, new_lead_id)
        self.assertEquals(new_lead.state, 'cancel')
        self.assertEquals(new_lead.user_id.id, self.admin)
        """ change the state of new_lead to done and check that responsible doen't change """
        new_lead.write({'state': 'done'})
        new_lead = self.model.browse(cr, uid, new_lead_id)
        self.assertEquals(new_lead.state, 'done')
        self.assertEquals(new_lead.user_id.id, self.admin)

    def test_02_check_from_draft_to_done_without_steps(self):
        """
        A new record will be created and will goes from draft to done in one operation
        We will create a rule that says in precondition that the record must be in the "draft" state while a postcondition filter says
        that the record will be done. If the state goes from 'draft' to 'done' the responsible will change. If those two conditions aren't
        verified, the responsible will stay the same
        The responsible in that test will change to user "demo"
        """
        cr, uid = self.cr, self.uid
        filter_draft = self.create_filter_draft(cr, uid)
        filter_done = self.create_filter_done(cr, uid)
        self.create_rule(cr, uid, filter_pre_id=filter_draft, filter_id=filter_done)
        new_lead_id = self.create_lead_test_1(cr, uid)
        new_lead = self.model.browse(cr, uid, new_lead_id)
        self.assertEquals(new_lead.state, 'draft')
        self.assertEquals(new_lead.user_id.id, self.admin)
        """ change the state of new_lead to done and check that responsible change to Demo_user"""
        new_lead.write({'state': 'done'})
        new_lead = self.model.browse(cr, uid, new_lead_id)
        self.assertEquals(new_lead.state, 'done')
        self.assertEquals(new_lead.user_id.id, self.demo)
