from django.core.management.base import BaseCommand

from core.models import FrequentlyAskedQuestion


class Command(BaseCommand):
    help = "Create 20 FAQ items with varying questions and answers."

    def handle(self, *args, **kwargs):
        questions = [
            "What is the purpose of this project?",
            "How do I install the application?",
            "What are the system requirements?",
            "Where can I find the user manual?",
            "Who do I contact for support?",
            "Is there a mobile version available?",
            "How do I reset my password?",
            "What is the refund policy?",
            "Can I use this app offline?",
            "How do I update my profile information?",
            "What file formats are supported?",
            "Is there a trial version available?",
            "How secure is the application?",
            "What are the premium features?",
            "Where can I find the terms and conditions?",
            "How do I delete my account?",
            "What is the pricing structure?",
            "Can I share my account with others?",
            "What languages does the app support?",
            "How do I provide feedback or suggestions?",
        ]

        answers = [
            "This project is designed to provide seamless integration and usability.",
            "To install, follow the steps in the installation guide provided on our website.",
            "The system requirements vary based on your platform; check the documentation for details.",
            "The user manual can be downloaded from the resources section.",
            "For support, email us at support@example.com or use the contact form.",
            "Yes, a mobile version is available on both iOS and Android stores.",
            "You can reset your password by clicking the 'Forgot Password' link on the login page.",
            "Refunds are processed as per our policy available on the website.",
            "The app has limited offline functionality; most features require internet access.",
            "Update your profile information by visiting the profile section in settings.",
            "Supported file formats include PDF, DOCX, and TXT.",
            "Yes, a trial version is available for 14 days with limited features.",
            "The application uses state-of-the-art security protocols to ensure data safety.",
            "Premium features include advanced analytics, customization options, and more.",
            "Terms and conditions are available on our legal page.",
            "To delete your account, navigate to settings and follow the account deletion process.",
            "Our pricing structure is tier-based; details are on the pricing page.",
            "No, sharing accounts is not allowed as per our terms of service.",
            "Currently, the app supports English, Spanish, and French.",
            "Provide feedback through the feedback form in the app or via email.",
        ]

        FrequentlyAskedQuestion.objects.bulk_create(
            [
                FrequentlyAskedQuestion(
                    question=questions[i], answer=answers[i], order=i + 1
                )
                for i in range(20)
            ]
        )

        self.stdout.write(self.style.SUCCESS("Successfully created 20 FAQ items."))
