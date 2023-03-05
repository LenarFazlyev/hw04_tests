from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post, User


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='author')
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

    def setUp(self):
        self.author_client = Client()
        self.author_client.force_login(self.author)
        self.auth_client = Client()
        self.auth_client.force_login(self.auth)
        # думаю логично urls перенести сюда, но не уверен что так практикуется.
        # если практикуется то повторы, которые ниже,
        # удалю, а здесь активирую.
        # urls: tuple = (
        #     ('posts:index', None, '/'),
        #     ('posts:group_posts',
        #      (self.group.slug,),
        #      f'/group/{self.group.slug}/'
        #      ),
        #     ('posts:profile', (self.auth,), f'/profile/{self.auth}/'),
        #     ('posts:post_detail',
        #      (self.post.pk,),
        #      f'/posts/{self.post.pk}/'
        #      ),
        #     ('posts:post_create', None, '/create/'),
        #     ('posts:post_edit',
        #      (self.post.pk,),
        #      f'/posts/{self.post.pk}/edit/'
        #      ),
        # )

    def test_pages_use_correct_templates(self):
        templates: tuple = (
            ('posts:index', None, 'posts/index.html'),
            ('posts:group_posts', (self.group.slug,), 'posts/group_list.html'),
            ('posts:profile', (self.auth,), 'posts/profile.html'),
            ('posts:post_detail', (self.post.pk,), 'posts/post_detail.html'),
            ('posts:post_create', None, 'posts/create_post.html'),
            ('posts:post_edit', (self.post.pk,), 'posts/create_post.html'),
        )
        for namespace, args, template in templates:
            with self.subTest(template=template):
                response = self.author_client.get(
                    reverse(namespace, args=args)
                )
                self.assertTemplateUsed(response, template)

    def test_post_404(self):
        response = self.client.get('/posts/2/')
        self.assertEqual(response.status_code, 404)

    def test_pages_uses_correct_urls(self):
        urls: tuple = (
            ('posts:index', None, '/'),
            ('posts:group_posts',
             (self.group.slug,),
             f'/group/{self.group.slug}/'
             ),
            ('posts:profile', (self.auth,), f'/profile/{self.auth}/'),
            ('posts:post_detail', (self.post.pk,), f'/posts/{self.post.pk}/'),
            ('posts:post_create', None, '/create/'),
            ('posts:post_edit',
             (self.post.pk,),
             f'/posts/{self.post.pk}/edit/'
             ),
        )

        for namespace, args, url in urls:
            with self.subTest(url=url):
                response = reverse(namespace, args=args)
                self.assertEqual(response, url)

    def test_urls_for_author(self):
        urls: tuple = (
            ('posts:index', None, '/'),
            ('posts:group_posts',
             (self.group.slug,),
             f'/group/{self.group.slug}/'
             ),
            ('posts:profile', (self.auth,), f'/profile/{self.auth}/'),
            ('posts:post_detail', (self.post.pk,), f'/posts/{self.post.pk}/'),
            ('posts:post_create', None, '/create/'),
            ('posts:post_edit',
             (self.post.pk,),
             f'/posts/{self.post.pk}/edit/'
             ),
        )

        for namespace, args, url in urls:
            with self.subTest(url=url):
                response = self.author_client.get(
                    reverse(namespace, args=args)
                )
                self.assertEqual(response.status_code, 200)

    def test_urls_for_auth(self):
        urls: tuple = (
            ('posts:index', None, '/'),
            ('posts:group_posts',
             (self.group.slug,),
             f'/group/{self.group.slug}/'
             ),
            ('posts:profile', (self.auth,), f'/profile/{self.auth}/'),
            ('posts:post_detail', (self.post.pk,), f'/posts/{self.post.pk}/'),
            ('posts:post_create', None, '/create/'),
            ('posts:post_edit',
             (self.post.pk,),
             f'/posts/{self.post.pk}/edit/'
             ),
        )

        for namespace, args, url in urls:
            with self.subTest(namespace=namespace, url=url):
                response = self.auth_client.get(reverse(namespace, args=args))
                if 'edit' in url:
                    self.assertRedirects(response, (f'/posts/{self.post.pk}/'))
                else:
                    self.assertEqual(response.status_code, 200)

    def test_urls_for_not_auth(self):
        urls: tuple = (
            ('posts:index', None, '/'),
            ('posts:group_posts',
             (self.group.slug,),
             f'/group/{self.group.slug}/'
             ),
            ('posts:profile', (self.auth,), f'/profile/{self.auth}/'),
            ('posts:post_detail', (self.post.pk,), f'/posts/{self.post.pk}/'),
            ('posts:post_create', None, '/create/'),
            ('posts:post_edit',
             (self.post.pk,),
             f'/posts/{self.post.pk}/edit/'
             ),
        )

        for namespace, args, url in urls:
            with self.subTest(namespace=namespace, url=url):
                response = self.client.get(
                    reverse(namespace, args=args), follow=True
                )
                if 'edit' in url or 'create' in url:
                    self.assertRedirects(
                        response, (f'/auth/login/?next={url}')
                    )
                else:
                    self.assertEqual(response.status_code, 200)
