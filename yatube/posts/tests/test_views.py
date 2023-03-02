# - Повторение кода проверки контекста для индекса, группы и профиля


from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from posts.models import Group, Post

User = get_user_model()
SHIFT_POST = 3


class PostPagesTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.auth = User.objects.create_user(username='auth')
        cls.auth_client = Client()
        cls.auth_client.force_login(cls.auth)
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.auth,
            text='Тестовый пост kjljf;sakdj;fskaj;flkjasd;klfjs;l',
            group=cls.group
        )

    def test_pages_uses_correct_template(self):
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_posts', kwargs={'slug': f'{self.group.slug}'}
            ): 'posts/group_list.html',
            reverse(
                'posts:profile', kwargs={'username': f'{self.auth}'}
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail', kwargs={'post_id': f'{self.post.pk}'}
            ): 'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse(
                'posts:post_edit',
                kwargs={'post_id': f'{self.post.pk}'}
            ): 'posts/create_post.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.auth_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_home_page_shows_correct_context(self):
        response = self.auth_client.get(reverse('posts:index'))
        self.assertEqual(response.context['page_obj'][0].text, self.post.text)
        self.assertEqual(
            response.context['page_obj'][0].author, self.post.author
        )
        self.assertEqual(response.context['page_obj'][0].group, self.group)

    def test_group_list_shows_correct_context(self):
        response = self.auth_client.get(
            reverse('posts:group_posts', kwargs={'slug': self.group.slug})
        )
        self.assertEqual(response.context['page_obj'][0].text, self.post.text)
        self.assertEqual(
            response.context['page_obj'][0].author, self.post.author
        )
        self.assertEqual(response.context['page_obj'][0].group, self.group)
        self.assertEqual(response.context['group'].title, self.group.title)
        self.assertEqual(response.context['group'].slug, self.group.slug)
        self.assertEqual(
            response.context['group'].description, self.group.description)

    def test_profile_page_shows_correct_context(self):
        response = self.auth_client.get(
            reverse('posts:profile', kwargs={'username': self.auth})
        )
        first_post: Post = response.context['page_obj'][0]
        self.assertEqual(first_post.text, self.post.text)
        self.assertEqual(first_post.author, self.post.author)
        self.assertEqual(first_post.group, self.group)
        self.assertEqual(
            response.context['author'].username, self.auth.username
        )

    def test_post_detail_page_shows_correct_context(self):
        response = self.auth_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.pk})
        )
        first_post = response.context['post']
        self.assertEqual(first_post.text, self.post.text)
        self.assertEqual(first_post.author, self.post.author)
        self.assertEqual(first_post.group, self.group)

    def test_create_post_shows_correct_context(self):
        response = self.auth_client.get(
            reverse('posts:post_create')
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_edit_post_shows_correct_context(self):
        response = self.auth_client.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk})
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.auth = User.objects.create_user(username='auth')
        cls.auth_client = Client()
        cls.auth_client.force_login(cls.auth)
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )

        for _ in range(settings.LIMITS_IN_PAGE + SHIFT_POST):
            Post.objects.create(
                author=cls.auth,
                text='Тестовый пост kjljf;sakdj;fskaj;flkjasd;klfjs;l',
                group=cls.group,
            )

    def test_index_correct_posts_numbers_on_page(self):
        for page in (1, 2):
            response = self.auth_client.get(
                reverse('posts:index'), [('page', page)]
            )
            if page == 1:
                self.assertEqual(
                    len(response.context['page_obj'].object_list),
                    settings.LIMITS_IN_PAGE
                )
            else:
                self.assertEqual(
                    len(response.context['page_obj'].object_list),
                    SHIFT_POST
                )
