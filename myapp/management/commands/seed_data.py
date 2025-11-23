"""
Management command to seed initial data (domains and tags)
Run: python manage.py seed_data
"""
from django.core.management.base import BaseCommand
from myapp.models import Domain, Tag


class Command(BaseCommand):
    help = 'Seed initial domains and tags'

    def handle(self, *args, **options):
        # Create Domains
        domains_data = [
            {'name': 'AI & Machine Learning', 'description': 'Artificial Intelligence and ML projects'},
            {'name': 'Web Development', 'description': 'Frontend and backend web applications'},
            {'name': 'Mobile Development', 'description': 'iOS, Android, and cross-platform apps'},
            {'name': 'Data Science', 'description': 'Data analysis and visualization'},
            {'name': 'Cybersecurity', 'description': 'Security and privacy projects'},
            {'name': 'Robotics', 'description': 'Robotics and automation'},
            {'name': 'IoT', 'description': 'Internet of Things projects'},
            {'name': 'Blockchain', 'description': 'Blockchain and cryptocurrency'},
            {'name': 'AR/VR', 'description': 'Augmented and Virtual Reality'},
            {'name': 'Biotech', 'description': 'Biotechnology and healthcare'},
            {'name': 'Design', 'description': 'UI/UX and graphic design'},
            {'name': 'Research', 'description': 'Academic and research projects'},
        ]

        for domain_data in domains_data:
            domain, created = Domain.objects.get_or_create(
                name=domain_data['name'],
                defaults={'description': domain_data['description']}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created domain: {domain.name}'))
            else:
                self.stdout.write(f'Domain already exists: {domain.name}')

        # Create Tags
        tags_data = [
            'Python', 'JavaScript', 'React', 'Node.js', 'Django', 'Flask',
            'Machine Learning', 'Deep Learning', 'TensorFlow', 'PyTorch',
            'Data Science', 'Pandas', 'NumPy', 'SQL', 'PostgreSQL',
            'MongoDB', 'Redis', 'Docker', 'Kubernetes', 'AWS',
            'React Native', 'Flutter', 'Swift', 'Kotlin', 'Java',
            'C++', 'Rust', 'Go', 'TypeScript', 'Vue.js',
            'Angular', 'Next.js', 'GraphQL', 'REST API', 'Microservices',
            'Cybersecurity', 'Penetration Testing', 'Cryptography',
            'Blockchain', 'Smart Contracts', 'Solidity', 'Web3',
            'AR', 'VR', 'Unity', 'Unreal Engine',
            'IoT', 'Raspberry Pi', 'Arduino', 'Embedded Systems',
            'UI/UX', 'Figma', 'Adobe XD', 'Design Systems',
            'Research', 'Academic', 'Publications', 'Open Source',
        ]

        for tag_name in tags_data:
            tag, created = Tag.objects.get_or_create(name=tag_name)
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created tag: {tag.name}'))
            else:
                self.stdout.write(f'Tag already exists: {tag.name}')

        self.stdout.write(self.style.SUCCESS('\nSuccessfully seeded domains and tags!'))

