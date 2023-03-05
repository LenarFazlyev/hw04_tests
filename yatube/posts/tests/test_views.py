from django import forms
from django.conf import settings
from django.test import Client, TestCase
from django.urls import reverse

from posts.forms import PostForm
from posts.models import Group, Post, User

SHIFT_POST = 3


class PostPagesTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.auth = User.objects.create_user(username='auth')
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

    def setUp(self) -> None:
        self.auth_client = Client()
        self.auth_client.force_login(self.auth)

    # То что ниже уберу после ревью. Я согласен с тобой, но в теории приводили
    # пример где проверки что URL-адрес использует шаблон делали во test_views.
    # Передай, пожалуйста коллегам мою обратную связь.
    # def test_pages_uses_correct_template(self):
    #     templates_pages_names = {
    #         reverse('posts:index'): 'posts/index.html',
    #         reverse(
    #             'posts:group_posts', args=({'slug': f'{self.group.slug}},)
    #         ): 'posts/group_list.html',
    #         reverse(
    #             'posts:profile', args=({'username': f'{self.auth}},)
    #         ): 'posts/profile.html',
    #         reverse(
    #             'posts:post_detail', args=({'post_id': f'{self.post.pk}},)
    #         ): 'posts/post_detail.html',
    #         reverse('posts:post_create'): 'posts/create_post.html',
    #         reverse(
    #             'posts:post_edit',
    #             args=({'post_id': f'{self.post.pk}},)
    #         ): 'posts/create_post.html',
    #     }
    #     for reverse_name, template in templates_pages_names.items():
    #         with self.subTest(reverse_name=reverse_name):
    #             response = self.auth_client.get(reverse_name)
    #             self.assertTemplateUsed(response, template)

    # Вернусь после ревью
    # def page_or_page_obj(self,true=False):
    #     urls: tuple = (
    #         ('posts:index', None,),
    #         # ('posts:group_posts', (self.group.slug,), ),
    #         # ('posts:profile', (self.auth,), ),
    #         # ('posts:post_detail', (self.post.pk,), ),
    #     )
    #     for name, args in urls:
    #         with self.subTest(name=name, args=args):
    #             response = self.auth_client.get(reverse(name, args=args))
    #             if true:
    #                 post = response.context['page']
    #             else:
    #                 post = response.context['page_obj'][0]
    #             self.assertEqual(post.text, self.post.text)

    # def test_strange(self):
    #     self.page_or_page_obj(False)

    def test_home_page_shows_correct_context(self):
        response = self.auth_client.get(reverse('posts:index'))
        self.assertEqual(response.context['page_obj'][0].text, self.post.text)
        self.assertEqual(
            response.context['page_obj'][0].author, self.post.author
        )
        self.assertEqual(response.context['page_obj'][0].group, self.group)

    def test_group_list_shows_correct_context(self):
        response = self.auth_client.get(
            reverse('posts:group_posts', args=(self.group.slug,))
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
            reverse('posts:profile', args=(self.auth,))
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
            reverse('posts:post_detail', args=(self.post.pk,))
        )
        first_post = response.context['post']
        self.assertEqual(first_post.text, self.post.text)
        self.assertEqual(first_post.author, self.post.author)
        self.assertEqual(first_post.group, self.group)

        # Нужно добавить пост не попал не в ту группу.
        # добавлю после ревью

    def test_create_and_edit_shows_correct_context(self):
        namespace_name: tuple = (
            ('posts:post_create', None, ),
            ('posts:post_edit', (self.post.pk,), ),
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for namespace, name in namespace_name:
            with self.subTest(namespace=namespace, name=name):
                response = self.auth_client.get(
                    reverse(namespace, args=(name))
                )
                self.assertIn('form', response.context)
                form = response.context.get('form')
                self.assertIsInstance(form, PostForm)
                for value, expected in form_fields.items():
                    with self.subTest(value=value):
                        form_field = response.context.get(
                            'form'
                        ).fields.get(value)
                        self.assertIsInstance(form_field, expected)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.auth = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )

        batch_size = settings.LIMITS_IN_PAGE + SHIFT_POST
        posts: list = []
        for i in range(batch_size):
            posts.append(Post(
                author=cls.auth,
                text='Тестовый пост kjljf;sakdj;fskaj;flkjasd;klfjs;l',
                group=cls.group,
            ))
        Post.objects.bulk_create(posts)

    def setUp(self) -> None:
        self.auth_client = Client()
        self.auth_client.force_login(self.auth)

    def test_index_correct_posts_numbers_on_page(self):
        names_args: tuple = (
            ('posts:index', None, ),
            ('posts:group_posts', (self.group.slug,), ),
            ('posts:profile', (self.auth,), ),
        )
        pages: tuple = (
            (1, 10),
            (2, 3)
        )

        for name, args in names_args:  # сложно дался мне это блок
            with self.subTest(name=name):
                for page, page_quantity in pages:
                    with self.subTest(page=page, page_quantity=page_quantity):
                        response = self.auth_client.get(
                            reverse(name, args=args), [('page', page) ,]
                        )
                        posts_on_pages = (
                            len(response.context['page_obj'].object_list)
                        )
                        self.assertEqual(posts_on_pages, page_quantity)
