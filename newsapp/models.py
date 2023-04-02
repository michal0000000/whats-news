
from django.utils.timezone import now
from django.db import models
from django import forms
from django.utils.safestring import mark_safe

class Category(models.Model):
    title = models.CharField(primary_key=True,max_length=50,default='N/A')
    display_title = models.CharField(max_length=50,default='N/A')
    active = models.BooleanField(default=False)
    visible = models.BooleanField(default=False)
    order = models.IntegerField(null=True)
    
    def __str__(self):
        return self.title
    
class Source(models.Model):
    name = models.CharField(primary_key=True,max_length=50)              # SME
    display_name = models.CharField(max_length=50)      # Dennik Sme
    pfp = models.CharField(max_length=512,default='static/images/default_source_20x20.png')              # pfp link         # homepage link
    scraping_link = models.CharField(max_length=512)    # scraping link
    category = models.ForeignKey(Category,on_delete=models.CASCADE,null=True)
    active = models.BooleanField(default=False)
    visible = models.BooleanField(default=False)
    
    def __str__(self):
        return self.name

# TODO: research GDPR, if neccessary dont store PI info (i.e. email)
class MembershipToken(models.Model):
    
    id = models.BigAutoField(primary_key=True)
    hashed_token = models.CharField(max_length=64) # sha256
    username = models.CharField(max_length=64,unique=True)
    email = models.CharField(max_length=64,unique=True)
    valid_until = models.DateTimeField()
    last_visit = models.DateTimeField(default=now)
    
    preferences = models.ManyToManyField(Source,through='MemberPreference',default=None)
    
    def __str__(self):
        return str(self.id)
    
    def set_last_visit(self,datetime):
        if self.last_visit < datetime:
            self.last_visit = datetime
            return True
        else:
            return False
    
    def check_token(self,submitted_token):
        return self.hashed_token == submitted_token
    
    class Meta:
        app_label = 'newsapp'
    
    """TODO:
        - def valid()
    """

class Author(models.Model):
    
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=50)
    
    def __str__(self):
        return self.name
    
class Tag(models.Model):
    
    id = models.BigAutoField(primary_key=True)
    title = models.CharField(max_length=50,default='N/A')
    
    
    def __str__(self):
        return self.title
    
class Article(models.Model):
    
    id = models.BigAutoField(primary_key=True)
    headline = models.CharField(max_length=256)
    headline_img = models.CharField(max_length=512,default='static/images/index.png')
    subtitle = models.TextField()
    link = models.CharField(max_length=512) 
    published = models.DateTimeField(blank=True)
    added = models.DateTimeField(default=now)
    source = models.ForeignKey(Source,on_delete=models.CASCADE,null=True)
    authors = models.ManyToManyField(Author)
    tags = models.ManyToManyField(Tag)
    
    # Return id of post
    def __str__(self):
        return self.headline
    
    # Get data needed for news feed page
    def get_feed_data(self):
        return {
            "id" : self.id,
            "headline" : self.headline,
            "image" : self.headline_img,
            "link" : self.link,
            "subtitle" : self.subtitle, 
            "published" : self.published,
            "added" : self.added,
            "source_display_name" : self.source.display_name,
            "source_pfp" : self.source.pfp,
            "source_link" : self.source.scraping_link,
            "authors" : self.authors.all(),
            "tags" : self.tags.all(),
        }
    
class UpcomingFeaturesForm(forms.Form):
    title = forms.CharField(label="Predmet", 
                            widget=forms.TextInput(attrs={'class':'flex bg-gray-50 rounded-lg shadow-lg focus:border focus:border-teal-400 px-6',
                                                          'cols':20}),
                            max_length=256)
    description = forms.CharField(label="Správa", 
                            widget=forms.Textarea(attrs={'class':'flex bg-gray-50 rounded-lg shadow-lg focus:border focus:border-teal-400',
                                                         'cols':22,
                                                         'rows':6}),
                            max_length=512)
      
class UpcomingFeatures(models.Model):
    id = models.BigAutoField(primary_key=True)
    title = models.CharField(max_length=256)
    description = models.CharField(max_length=512,null=True)
    visible = models.BooleanField(default=False)
    votes = models.ManyToManyField(MembershipToken,default=None)
    submitted = models.DateField(default=now)
    
    def __str__(self):
        return str(self.id)
    
    def get_upcoming_features_data(self):
        return {
            'id' : self.id,
            'title' : self.title,
            'desc' : self.description,
            'votes' : self.votes.count(),
            'first' : False
        }
        
class MemberPreference(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=50,blank=True) # 'username_source'
    member = models.ForeignKey(MembershipToken,on_delete=models.CASCADE)
    sources = models.ForeignKey(Source,on_delete=models.CASCADE,blank=True,null=True)
    display_in_feed = models.BooleanField(default=True)
       
class SourcesCheckboxSelectMultiple(forms.CheckboxSelectMultiple):
    def render(self, name, value, attrs=None, renderer=None):
        output = []
        for pref_id, src_name, src_pfp, cat_title, checked in self.choices:
            output.append(f"""
                          <tr>
                                <td class="p-4 whitespace-nowrap">
                                    <div class="flex items-center h-10">
                                        <div class="w-10 flex-shrink-0"><img class="rounded-none m-auto" src="{src_pfp}" alt="{src_name}"></div>
                                        <div class="font-medium ml-3 text-gray-800">{src_name}</div>
                                    </div>
                                </td>
                                <td class="p-2 whitespace-nowrap">
                                    <div class="text-left">{cat_title}</div>
                                </td>
                                <td class="p-2 whitespace-nowrap">
                                    <div class="text-left font-medium text-green-500">
                                        
                                        <input type="checkbox" id="{pref_id}" name="choice" value="{pref_id}" {checked} />
                                    
                                    </div>
                                </td>
                                </tr>
                          """)
        return mark_safe('\n'.join(output))

class SourceManagementDynamicForm(forms.Form):
    def __init__(self, choices, *args, **kwargs):
        super(SourceManagementDynamicForm, self).__init__(*args, **kwargs)
        self.fields['choices_field'] = forms.MultipleChoiceField( # used to be MultipleChoiceField here
            choices=choices,
            widget=SourcesCheckboxSelectMultiple,
            required=False,
            label="",
            label_suffix=None
        )   
    
    def validate_choices(self,form_data):    
        # Extract selected sources
        result = [int(x) for x in form_data.getlist('choice')]

        # Validate selected sources
        validation_queryset = MemberPreference.objects.filter(pk__in=result)
        if len(result) != len(validation_queryset):
            return False
        else:
            return result
                    