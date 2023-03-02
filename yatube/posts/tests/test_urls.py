from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from posts.models import Group, Post

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()
        cls.author = User.objects.create_user(username='author')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)

        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый пост kjljf;sakdj;fskaj;flkjasd;klfjs;l',
        )

        cls.auth = User.objects.create_user(username='auth')
        cls.auth_client = Client()
        cls.auth_client.force_login(cls.auth)

    def test_urls_and_templates(self):
        urls = [
            ('/', 200, 'posts/index.html'),
            (f'/group/{self.group.slug}/', 200, 'posts/group_list.html'),
            (f'/profile/{self.auth}/', 200, 'posts/profile.html'),
            (f'/posts/{self.post.pk}/', 200, 'posts/post_detail.html'),
            # ('/posts/2/', 404, 'help.html'),
            # пока не нашел возможен ли такой вариант и
            # какой "шаблон" нужно указать чтобы тест
            # не ломался. Если знаешь как, подскажи.
            # Заранее спасибо. Пока отдельный тест ниже
        ]

        for url, status, template in urls:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, status)
                self.assertTemplateUsed(response, template)

    def test_post_404(self):
        response = self.guest_client.get('/posts/2/')
        self.assertEqual(response.status_code, 404)

    def test_create_url_exist_at_desired_location_authorized(self):
        response = self.auth_client.get('/create/')
        self.assertEqual(response.status_code, 200)

    def test_create_url_redirect_anonymous_on_admin_login(self):
        response = self.guest_client.get('/create/', follow=True)
        self.assertRedirects(response, ('/auth/login/?next=/create/'))

    def test_edit_url_exist_at_desired_location_author(self):
        response = self.author_client.get(f'/posts/{self.post.pk}/edit/')
        self.assertEqual(response.status_code, 200)

    def test_edit_url_redirect_anonymous_on_admin_login(self):
        response = self.guest_client.get(
            f'/posts/{self.post.pk}/edit/',
            follow=True
        )
        self.assertRedirects(response, ('/auth/login/?next=/posts/1/edit/'))

    def test_edit_url_redirect_auth_on_admin_login(self):
        response = self.auth_client.get(
            f'/posts/{self.post.pk}/edit/',
            follow=True
        )
        self.assertRedirects(response, (f'/posts/{self.post.pk}/'))

    def test_edit_url_uses_correct_template_author(self):
        response = self.author_client.get(f'/posts/{self.post.pk}/edit/')
        self.assertTemplateUsed(response, 'posts/create_post.html')

    def test_create_url_uses_correct_template_auth(self):
        response = self.auth_client.get('/create/')
        self.assertTemplateUsed(response, 'posts/create_post.html')
