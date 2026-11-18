from django.db import migrations

def populate_nasarawa_orgs(apps, schema_editor):
    SupportOrganization = apps.get_model('advisor', 'SupportOrganization')
    orgs = [
        {
            'name': 'NSUK University Health Services (Campus Clinic)',
            'category': 'medical',
            'state': 'Nasarawa',
            'phone_number': '08036001122',
            'alt_phone_number': '08023456789',
            'email': 'healthservices@nsuk.edu.ng',
            'address': 'Main Campus, Keffi - Akwanga Expressway, Keffi, Nasarawa State',
            'website': 'https://nsuk.edu.ng',
            'description': 'Official university medical clinic offering immediate 24/7 post-assault emergency medical treatment, STI preventative prophylaxis (PEP), and confidential trauma referral for students and staff.',
            'is_verified': True
        },
        {
            'name': 'NSUK Security Directorate & Rapid Response Unit',
            'category': 'helpline',
            'state': 'Nasarawa',
            'phone_number': '08023456789',
            'alt_phone_number': '08031234567',
            'email': 'security@nsuk.edu.ng',
            'address': 'Security Headquarters, Senate Building, Main Campus, Keffi',
            'website': 'https://nsuk.edu.ng',
            'description': '24/7 campus security patrol and emergency response division. Provides immediate physical protection, safe escorts, and swift investigation coordination across all NSUK campuses.',
            'is_verified': True
        },
        {
            'name': 'NSUK Centre for Gender Studies & Counseling Desk',
            'category': 'counseling',
            'state': 'Nasarawa',
            'phone_number': '08031112233',
            'email': 'genderstudies@nsuk.edu.ng',
            'address': 'Centre for Gender Studies, Faculty of Social Sciences Annex, NSUK, Keffi',
            'website': 'https://nsuk.edu.ng',
            'description': 'Dedicated campus counseling center providing empathetic trauma therapy, psycho-social healing, confidential anti-harassment reporting, and academic accommodation advocacy.',
            'is_verified': True
        },
        {
            'name': 'FIDA Nasarawa State (Federation of Women Lawyers)',
            'category': 'legal',
            'state': 'Nasarawa',
            'phone_number': '08037004455',
            'email': 'fidanasarawa@fida.org.ng',
            'address': 'High Court of Justice Complex, Shendam Road, Lafia, Nasarawa State',
            'description': 'Provides pro-bono legal advocacy, free court representation, and prosecution assistance under the VAPP Act for female students and victims of domestic or sexual violence.',
            'is_verified': True
        },
        {
            'name': 'Nasarawa State Ministry of Women Affairs GBV Desk',
            'category': 'helpline',
            'state': 'Nasarawa',
            'phone_number': '08069998877',
            'email': 'womenaffairs@nasarawastate.gov.ng',
            'address': 'State Secretariat Complex, Jos Road, Lafia, Nasarawa State',
            'description': 'State government crisis response desk coordinating emergency safe house placement, social rehabilitation, and multi-agency legal and medical referrals.',
            'is_verified': True
        },
        {
            'name': 'Dalhatu Araf Specialist Hospital (DASH) SARC Unit',
            'category': 'medical',
            'state': 'Nasarawa',
            'phone_number': '08055554433',
            'address': 'DASH Hospital Complex, Makurdi Road, Lafia, Nasarawa State',
            'description': 'Tertiary government medical institution offering comprehensive forensic examinations, emergency contraception, HIV PEP, and clinical psychological care.',
            'is_verified': True
        }
    ]
    for org_data in orgs:
        SupportOrganization.objects.get_or_create(
            name=org_data['name'],
            defaults=org_data
        )

def rollback_nasarawa_orgs(apps, schema_editor):
    pass

class Migration(migrations.Migration):
    dependencies = [
        ('advisor', '0002_populate_data'),
    ]

    operations = [
        migrations.RunPython(populate_nasarawa_orgs, rollback_nasarawa_orgs),
    ]
