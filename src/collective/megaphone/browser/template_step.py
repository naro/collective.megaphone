from collective.megaphone.compat import IAdding
from collective.megaphone.compat import ViewPageTemplateFile
from collective.megaphone.utils import DOMAIN, MegaphoneMessageFactory as _
from collective.megaphone.config import ANNOTATION_KEY, RECIPIENT_MAILER_ID, DEFAULT_LETTER_TEMPLATE
from collective.z3cform.wizard import wizard
from persistent.dict import PersistentDict
from z3c.form import field
from zope import schema
from zope.interface import Interface
from zope.annotation.interfaces import IAnnotations
from Products.CMFPlone.utils import safe_unicode
from Products.CMFPlone.i18nl10n import utranslate


class ITemplateStep(Interface):
    subject = schema.TextLine(
        title = _(u'E-mail subject'),
        description = _(u'Enter the template for the e-mail subject. You may use the listed variables.'),
        )
    
    template = schema.Text(
        title = _(u'Letter Text'),
        description = _(u'Enter the text of the letter. You may use the listed variables.'),
        )

class TemplateStep(wizard.Step):
    template = ViewPageTemplateFile('template_step.pt')
    
    prefix = 'template'
    label = _(u'Letter to Decisionmaker(s)')
    description = _(u"This step allows you to configure the subject and text of the message " +
                    u"which will be sent to each of the recipients.")
    fields = field.Fields(ITemplateStep)

    def update(self):
        wizard.Step.update(self)
        self.widgets['subject'].size = 50
        self.widgets['template'].rows = 10

    def getVariables(self):
        fields = self.wizard.session['formfields']['fields']
        ignored_fields = ('sincerely', )
        vars = [('sender_%s' % f_id, _(u"Sender's $varname", mapping={'varname': f['title']}))
            for f_id, f in sorted(fields.items(), key=lambda x:x[1]['order'])
            if f_id not in ignored_fields]
        vars += (
            ('recip_honorific', _(u"Recipient's Honorific")),
            ('recip_first', _(u"Recipient's First")),
            ('recip_last', _(u"Recipient's Last")),
            )
        return [dict(title=title, id=id) for id, title in vars]
    
    def initialize(self):
        data = self.getContent()
        if 'subject' not in data:
            data['subject'] = utranslate(DOMAIN,
                _(u'Dear ${recip_honorific} ${recip_first} ${recip_last}'),
                context=self.request)
        if 'template' not in data:
            data['template'] = utranslate(DOMAIN, DEFAULT_LETTER_TEMPLATE, context=self.request)
        self.wizard.sync()
    
    def apply(self, pfg, initial_finish=True):
        data = self.getContent()
        annotation = IAnnotations(pfg).setdefault(ANNOTATION_KEY, PersistentDict())
        annotation['template'] = data['template']
        mailer = getattr(pfg, RECIPIENT_MAILER_ID)
        mailer.setMsg_subject(data['subject'])
        if not mailer.getRawSenderOverride():
            mailer.setSenderOverride('here/@@letter-mailer-renderer/sender_envelope')
        if not mailer.getRawSubjectOverride():
            mailer.setSubjectOverride('here/@@letter-mailer-renderer/render_subject')
    
    def load(self, pfg):
        data = self.getContent()
        if IAdding.providedBy(pfg):
            return data
        data['template'] = IAnnotations(pfg).get(ANNOTATION_KEY, {}).get('template', '')
        mailer = getattr(pfg, RECIPIENT_MAILER_ID, None)
        if mailer is not None:
            data['subject'] = safe_unicode(mailer.getMsg_subject())
