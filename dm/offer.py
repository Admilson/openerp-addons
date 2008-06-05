import time
import offer_step

from osv import fields
from osv import osv

AVAILABLE_STATES = [
    ('draft','Draft'),
    ('open','Open'),
    ('freeze', 'Freeze'),
    ('closed', 'Close')
]

AVAILABLE_TYPE = [
    ('model','Model'),
    ('new','New'),
    ('standart','Standart'),
    ('rewrite','Rewrite'),
]


class dm_media(osv.osv):
    _name = "dm.media"
    _columns = {
        'name' : fields.char('Media', size=64, required=True),
    }
    
dm_media()

class dm_preoffer(osv.osv):
    _name = "dm.preoffer"
    _columns = {    
        'name' : fields.char("Name",size=64,required=True),
        'code' : fields.char("Code",size=64,required=True),
        'creator_id' : fields.many2one('res.partner','Creator'),
        'copywriter_id' : fields.many2one('res.partner','Ordered To'),
        'market_id' : fields.many2one('res.country','Market'),
        'media_id' : fields.many2one('dm.media','Media',ondelete="cascade"),
        'type' : fields.selection([('new','New'),('rewrite','Rewrite')],'Type'),
        'order_number' : fields.char('Order Number',size=16),
        'order_date' : fields.date('Order Date'),
        'plannned_delivery_date' : fields.date('Planned Delivery Date') ,
        'delivery_date' : fields.date('Delivery Date'),
        'summary' : fields.text('Summary'),
        'state' : fields.selection([('free','Free'),('assigned','Assigned')],"State",readonly=True),
    }
    
    _defaults = {
        'state': lambda *a: 'free',    
    }
    def go_to_offer(self,cr, uid, ids, *args):
        res = self.browse(cr,uid,ids)[0]
        if res.market_id:
            country = [[6,0,[res.market_id.id]]]
        else :
            country =[]
        vals = {
                'name':res.name,
                'type':res.type,
                'order_date':res.order_date,
                'plannned_delivery_date':res.plannned_delivery_date,
                'delivery_date' : res.delivery_date,
                'desc':res.summary,
                'code':res.code,
                'trademark_country_ids':country,
                'copywriter_id':res.copywriter_id.id,
                'offer_responsible_id':res.creator_id.id,
                'preoffer_id':res.id
            }
        self.pool.get('dm.offer').create(cr,uid,vals)
        self.write(cr,uid,ids,{'state':'assigned'})
        return True
dm_preoffer()

class dm_offer_category(osv.osv):
    _name = "dm.offer.category"
    _rec_name = "name"
    
    def name_get(self, cr, uid, ids, context={}):
        if not len(ids):
            return []
        reads = self.read(cr, uid, ids, ['name','parent_id'], context)
        res = []
        for record in reads:
            name = record['name']
            if record['parent_id']:
                name = record['parent_id'][1]+' / '+name
            res.append((record['id'], name))
        return res

    def _name_get_fnc(self, cr, uid, ids, prop, unknow_none, unknow_dict):
        res = self.name_get(cr, uid, ids)
        return dict(res)
    
    def _check_recursion(self, cr, uid, ids):
        level = 100
        while len(ids):
            cr.execute('select distinct parent_id from dm_offer_category where id in ('+','.join(map(str,ids))+')')
            ids = filter(None, map(lambda x:x[0], cr.fetchall()))
            if not level:
                return False
            level -= 1
        return True     

    _columns = {
        'complete_name' : fields.function(_name_get_fnc, method=True, type='char', string='Category'),
        'parent_id' : fields.many2one('dm.offer.category', 'Parent'),
        'name' : fields.char('Name', size=64, required=True),
        'child_ids': fields.one2many('dm.offer.category', 'parent_id', 'Childs Category'),
        'domain' : fields.selection([('model','Model'),('general','General'),('production','Production'),('purchase','Purchase')], 'Category Domain')
    }
    
    _constraints = [
        (_check_recursion, 'Error ! You can not create recursive categories.', ['parent_id'])
    ]
        
dm_offer_category()

class dm_offer_production_cost(osv.osv):
    _name = "dm.offer.production.cost"
    _columns = {
        'name' : fields.char('Name', size=32, required=True)
    }               
    
dm_offer_production_cost()

class dm_offer_delay(osv.osv):
    _name = "dm.offer.delay"
    _columns = {
        'name' : fields.char('Name', size=32, required=True),
		'value' : fields.integer('Number of days'),
    }
    
dm_offer_delay()


class dm_customer(osv.osv):
    _name = "dm.customer"
    _inherit = 'res.partner'
    _columns = {
        'customer_number' : fields.char('Customer Number',size=16),
        'language_id' : fields.many2one('res.lang','Main Language'),
        'language_ids' : fields.many2many('res.lang','dm_customer_langs','lang_id','customer_id','Other Languages'),
        'prospect_media_ids' : fields.many2many('dm.media','dm_customer_prospect_media','prospect_media_id','customer_id','Prospect for Media'),
        'client_media_ids' : fields.many2many('dm.media','dm_customer_client_media','client_media_id','customer_id','Client for Media'),
    }
dm_customer()

class dm_customer_offer(osv.osv):
    _name = "dm.customer.offer"
    _columns ={
        'customer_id' : fields.many2one('dm.customer', 'Customer', ondelete='cascade'),
        'customer_number' : fields.char('Customer Number',size=16),
        'title' : fields.char('Title',size=16),
        'customer_firstname' : fields.char('First Name', size=16),
        'customer_lastname' : fields.char('Last Name', size=16),
        'customer_add1' : fields.char('Address1', size=16),
        'customer_add2' : fields.char('Address2', size=16),
        'customer_add3' : fields.char('Address3', size=16),
        'customer_add4' : fields.char('Address4', size=16),
        'country' : fields.char('Country', size=16),
        'zip' : fields.char('Zip Code', size=12),
        'zip_summary' : fields.char('Zip Summary', size=64),
        'distribution_office' : fields.char('Distribution Office', size=64),
        'action_code' : fields.char('Action Code', size=16),
#        'offer_step' : fields.many2one('dm.offer.step', 'Offer Step', ondelete="cascade"),
        'offer_step' : fields.char('Offer Step', size=16),
        'raw_datas' : fields.char('Raw Datas', size=16),
    }
    
    def onchange_rawdatas(self,cr,uid,ids,raw_datas):
        if not raw_datas:
            return {}
        raw_datas = "2;00573G;168120;MISS;Lever;Shirley;W Sussex;;25 Oxford Road;;GBR;BN;BN11 1XQ;WORTHING.LU.SX"
        value = raw_datas.split(';')
        key = ['datamatrix_type','action_code','customer_number','title','customer_lastname','customer_firstname','customer_add1','customer_add2','customer_add3','customer_add4','country','zip_summary','zip','distribution_office']
        value = dict(zip(key,value))
        if value['customer_number']:
            dm_customer = self.pool.get('dm.customer').search(cr,uid,[('customer_number','=',value['customer_number'])])
            if dm_customer:
                value['customer_id']=dm_customer[0]
        return {'value':value}
    
    def set_confirm(self, cr, uid, ids, *args):
        return True
dm_customer_offer()

class dm_offer(osv.osv):
    _name = "dm.offer"
    _rec_name = 'name'

    def __history(self, cr, uid, cases, keyword, context={}):
        for case in cases:
            data = {
                'date' : time.strftime('%Y-%m-%d'),
                'user_id': uid,
                'state' : keyword,
                'offer_id': case.id
            }
            obj = self.pool.get('dm.offer.history')
            obj.create(cr, uid, data, context)
        return True

    def dtp_last_modification_date(self, cr, uid, ids, field_name, arg, context={}):
        result={}
        for id in ids:
            sql = "select write_date,create_date from dm_offer where id = %d"%id
            cr.execute(sql)
            res = cr.fetchone()
            print res[1]
            if res[0]:
                result[id]=res[0].split(' ')[0]
            else :
                result[id]=res[1].split(' ')[0]
        return result
    _columns = {
        'name' : fields.char('Name', size=64, required=True),
        'code' : fields.char('Code', size=16, required=True),
        'lang_orig' : fields.many2one('res.lang', 'Original Language'),
        'copywriter_id' : fields.many2one('res.partner', 'Copywriter'),
#        'step_ids' : fields.one2many('dm.offer.step','offer_id','Offer Steps'),
        'offer_responsible_id' : fields.many2one('res.users','Responsible',ondelete="cascade"),
        'recommended_trademark' : fields.many2one('dm.trademark','Recommended Trademark'),
        'offer_origin_id' : fields.many2one('dm.offer', 'Original Offer'),
        'active' : fields.boolean('Active'),
        'quotation' : fields.char('Quotation', size=16),
        'legal_state' : fields.selection([('validated','Validated'), ('notvalidated','Not Validated'), ('inprogress','In Progress'), ('refused','Refused')],'Legal State'),
        'category_ids' : fields.many2many('dm.offer.category','dm_offer_category_rel', 'offer_id', 'offer_category_id', 'Categories', domain="[('domain','=','general')]"),
        'notes' : fields.text('General Notes'),
        'state': fields.selection(AVAILABLE_STATES, 'Status', size=16, readonly=True),
        'desc' : fields.text('Description'),
        'dtp_note' : fields.text('DTP Notes'),
        'dtp_category_ids' : fields.many2many('dm.offer.category','dm_offer_dtp_category','offer_id','offer_dtp_categ_id', 'DTP Categories') ,# domain="[('domain','=','production')]"),
        'trademark_note' : fields.text('Trademark Notes'),
        'trademark_category_ids' : fields.many2many('dm.offer.category','dm_offer_trademark_category','offer_id','offer_trademark_categ_id','Trademark Categories'),# domain="[('domain','=','purchase')]"),
        'production_note' : fields.text('Production Notes'),
        'purchase_note' : fields.text('Purchase Notes'),
        'type' : fields.selection(AVAILABLE_TYPE, 'Type', size=16),
        'production_category_ids' : fields.many2many('dm.offer.category','dm_offer_production_category','offer_id','offer_production_categ_id', 'Production Categories' , domain="[('domain','=','production')]"),
        'production_delay' : fields.many2one('dm.offer.delay', 'Delay'),
        'production_cost' : fields.many2one('dm.offer.production.cost', 'Production Cost'),
        'purchase_note' : fields.text('Purchase Notes'),
        'purchase_category_ids' : fields.many2many('dm.offer.category','dm_offer_purchase_category','offer_id','offer_purchase_categ_id', 'Purchase Categories', domain="[('domain','=','purchase')]"),
        'history_ids' : fields.one2many('dm.offer.history', 'offer_id', 'History', ondelete="cascade"),
        'order_date' : fields.date('Order Date'),
        'last_modification_date' : fields.function(dtp_last_modification_date, method=True,type="char", string='Last Modification Date',readonly=True),
        'plannned_delivery_date' : fields.date('Planned Delivery Date'),
        'delivery_date' : fields.date('Delivery Date'),
        'fixed_date' : fields.date('Fixed Date'),
        'buffer_delay' : fields.integer('Buffer Delay'),
        'trademark_sex' : fields.selection([('all','All'),('female','Female'),('male','male')],"Sex"), 
        'trademark_age' : fields.integer('Age'),        
        'trademark_country_ids' : fields.many2many('res.country','dm_offer_trademark_country', 'offer_id', 'country_id', 'Nationality'),
        'forbidden_country_ids' : fields.many2many('res.country','dm_offer_forbidden_country', 'offer_id', 'country_id', 'Forbidden Countries'),
        'forbidden_state_ids' : fields.many2many('res.country.state','dm_offer_forbidden_state', 'offer_id', 'state_id', 'Forbidden States'),
        'preoffer_id' : fields.many2one('dm.preoffer','Preoffer'),
#       (still to be defined by the client)
    }
    
    _defaults = {
        'active': lambda *a: 1,
        'state': lambda *a: 'draft',
        'type': lambda *a: 'new',
        'legal_state': lambda *a: 'validated',
    }

    def state_close_set(self, cr, uid, ids, *args):
        cases = self.browse(cr, uid, ids)
        cases[0].state 
        self.__history(cr,uid, cases, 'closed')
        self.write(cr, uid, ids, {'state':'closed'})
        return True  

    def state_open_set(self, cr, uid, ids, *args):
        cases = self.browse(cr, uid, ids)
        cases[0].state 
        self.__history(cr,uid, cases, 'open')
        self.write(cr, uid, ids, {'state':'open'})
        return True 
    
    def state_freeze_set(self, cr, uid, ids, *args):
        cases = self.browse(cr, uid, ids)
        cases[0].state 
        self.__history(cr,uid, cases, 'freeze')
        self.write(cr, uid, ids, {'state':'freeze'})
        return True
    
    def state_draft_set(self, cr, uid, ids, *args):
        cases = self.browse(cr, uid, ids)
        cases[0].state 
        self.__history(cr,uid, cases, 'draft')
        self.write(cr, uid, ids, {'state':'draft'})
        return True  
dm_offer()

class dm_offer_history(osv.osv):
    _name = "dm.offer.history"
    _order = 'date'
    _columns = {
        'offer_id' : fields.many2one('dm.offer', 'Offer', required=True, ondelete="cascade"),
        'date' : fields.date('Date'),
        'user_id' : fields.many2one('res.users', 'User'),
        'state': fields.selection(AVAILABLE_STATES, 'Status', size=16)
    }
    _defaults = {
        'date': lambda *a: time.strftime('%Y-%m-%d'),
    }

dm_offer_history()
