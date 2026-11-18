from django.db import migrations

def populate_organizations(apps, schema_editor):
    SupportOrganization = apps.get_model('advisor', 'SupportOrganization')
    
    orgs = [
        # --- LAGOS STATE ---
        {
            'name': 'Lagos State Domestic and Sexual Violence Agency (DSVA)',
            'category': 'helpline',
            'state': 'Lagos',
            'phone_number': '08003333333',
            'alt_phone_number': '08137960048',
            'email': 'info@dsvrtlagos.org',
            'address': 'DSVA Secretariat, Alausa, Ikeja, Lagos State',
            'website': 'https://www.dsvrtlagos.org',
            'description': 'State agency providing rapid emergency response, legal protection, rescue, and psychological counseling for domestic and sexual violence victims.',
            'is_verified': True,
        },
        {
            'name': 'Mirabel Centre',
            'category': 'medical',
            'state': 'Lagos',
            'phone_number': '08172401444',
            'alt_phone_number': '08187870000',
            'email': 'info@mirabelcentre.org',
            'address': 'Lagos State University Teaching Hospital (LUTH), Idi-Araba, Surulere, Lagos',
            'website': 'https://www.mirabelcentre.org',
            'description': 'First Sexual Assault Referral Centre (SARC) in Nigeria. Offers free, confidential forensic medical treatment, emergency contraception, and trauma counseling for survivors.',
            'is_verified': True,
        },
        {
            'name': "Sophia's Place (Project Alert Shelter)",
            'category': 'shelter',
            'state': 'Lagos',
            'phone_number': '08052004856',
            'alt_phone_number': '08180091072',
            'email': 'projectalert@projectalertnig.org',
            'address': 'Ojodu-Berger area, Lagos State (exact address protected for security)',
            'website': 'https://www.projectalertnig.org',
            'description': 'Provides safe shelter, security, emergency housing, legal support, and trauma therapy for women fleeing domestic violence.',
            'is_verified': True,
        },
        {
            'name': "Women's Rights Advancement and Protection Alternative (WRAPA) - Lagos",
            'category': 'legal',
            'state': 'Lagos',
            'phone_number': '08033202545',
            'email': 'info@wrapanigeria.org',
            'address': 'Yaba, Lagos State',
            'website': 'https://wrapanigeria.org',
            'description': 'NGO offering legal advocacy, free legal representation, mediation, and safety awareness campaigns for female victims of abuse and violence.',
            'is_verified': True,
        },
        
        # --- ABUJA / FCT ---
        {
            'name': 'National Human Rights Commission (NHRC) GBV Toll-Free Line',
            'category': 'helpline',
            'state': 'FCT',
            'phone_number': '08006472468',
            'alt_phone_number': '09033333222',
            'email': 'info@nhrc.gov.ng',
            'address': '19 Aguiyi Ironsi Street, Maitama, Abuja',
            'website': 'https://www.nhrc.gov.ng',
            'description': 'Official government helpline to report gender-based violence, domestic abuse, human trafficking, and discrimination. Initiates legal actions.',
            'is_verified': True,
        },
        {
            'name': 'Cece Yara Foundation',
            'category': 'counseling',
            'state': 'FCT',
            'phone_number': '08002223333',
            'email': 'info@ceceyara.org',
            'address': 'Maitama District, Abuja',
            'website': 'https://www.ceceyara.org',
            'description': 'Child advocacy center offering toll-free crisis helpline, counseling, forensic investigations, and child abuse rescue services.',
            'is_verified': True,
        },
        {
            'name': 'FCT Sexual Assault Referral Centre (SARC)',
            'category': 'medical',
            'state': 'FCT',
            'phone_number': '08035985002',
            'address': 'Wuse District Hospital, Wuse Zone 3, Abuja',
            'description': 'Provides free, post-assault medical checks, preventative medication for STIs, and forensic testing along with counseling support.',
            'is_verified': True,
        },

        # --- KANO STATE ---
        {
            'name': 'Waraka Sexual Assault Referral Centre (SARC)',
            'category': 'medical',
            'state': 'Kano',
            'phone_number': '08091113222',
            'address': 'Murtala Muhammad Specialist Hospital, Kano City, Kano State',
            'description': 'Comprehensive medical center offering free emergency medical care, diagnostic checkups, post-exposure prophylaxis (PEP), and mental counseling.',
            'is_verified': True,
        },
        {
            'name': 'FIDA Kano (International Federation of Women Lawyers)',
            'category': 'legal',
            'state': 'Kano',
            'phone_number': '08037001402',
            'address': 'Court Road, Gyadi-Gyadi, Kano City, Kano State',
            'description': 'Professional network of female lawyers providing free legal aid, counseling, and judicial representation for women and children facing violence.',
            'is_verified': True,
        },

        # --- RIVERS STATE ---
        {
            'name': 'Rose Centre SARC (Rivers State)',
            'category': 'medical',
            'state': 'Rivers',
            'phone_number': '09062061245',
            'address': 'Rivers State University Teaching Hospital (RSUTH), Port Harcourt, Rivers State',
            'description': 'Offers free forensic screening, emergency medical treatments, pregnancy preventions, and empathetic counseling to survivors of assault.',
            'is_verified': True,
        },
        {
            'name': 'Medical Women Association of Nigeria (MWAN) GBV Desk - Rivers',
            'category': 'counseling',
            'state': 'Rivers',
            'phone_number': '08033131333',
            'address': 'MWAN Secretariat, Port Harcourt, Rivers State',
            'description': 'Offers specialized therapy, psychological triage, group counseling sessions, and general wellness checks for abuse victims.',
            'is_verified': True,
        }
    ]

    for org_data in orgs:
        SupportOrganization.objects.get_or_create(
            name=org_data['name'],
            defaults=org_data
        )

class Migration(migrations.Migration):
    dependencies = [
        ('advisor', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(populate_organizations),
    ]
