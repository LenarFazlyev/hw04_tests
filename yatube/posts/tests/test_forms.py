from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse

from ..forms import PostForm
from ..models import Group, Post, User


class PostCreateAndEditFormsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='author')

        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.group_new = Group.objects.create(
            title='Тестовая группа два',
            slug='test-slugtwo',
            description='Тестовое описание два',
        )
        cls.form = PostForm()

    def setUp(self):
        self.author_client = Client()
        self.author_client.force_login(self.author)
        self.post = Post.objects.create(
            author=self.author,
            text='Тестовый пост нумер ван',
            group=self.group
        )

    def test_create_post_authorized(self):
        """Тест возможность создания поста авторизированным клиентом"""
        form_data = {
            'group': self.group.id,
            'text': 'Тестовый текст нумер ту',
        }
        # Убедился что пост один в базе, до создания еще одного.
        Post.objects.all().delete()
        self.assertEqual(Post.objects.count(), 0)
        response = self.author_client.post(
            reverse('posts:post_create'),
            data=form_data
        )
        self.assertRedirects(
            response,
            reverse(
                'posts:profile',
                args=(self.author.username,),
            ),
        )
        self.assertEqual(Post.objects.count(), 1)
        post = Post.objects.first()
        self.assertEqual(
            post.author, self.author
        )  # автор
        self.assertEqual(
            post.group.pk, form_data['group']
        )  # группа
        self.assertEqual(
            post.text, form_data['text']
        )  # текст

    def test_create_post_not_authorized(self):
        """Тестирование невозможности создания поста гостем"""
        post_count = Post.objects.count()
        form_data = {
            'group': self.group.id,
            'text': 'Тестовый текст нумер трии',
        }
        # Убедился что пост один в базе, до создания еще одного.
        self.assertEqual(Post.objects.count(), 1)
        response = self.client.post(
            reverse('posts:post_create'), data=form_data
        )
        # Убедился что количество постов не изменилось
        self.assertEqual(Post.objects.count(), post_count)
        # Убедился что не авторизованный получил редирект
        self.assertEqual(response.status_code, 302)

    def test_edit_post_authorized(self):
        """Тестирование редактирования поста пользователем"""
        posts_count = Post.objects.count()
        form_data = {
            'group': self.group_new.id,
            'text': 'Отредактированный пост',
        }

        response = self.author_client.post(
            reverse(
                'posts:post_edit',
                args=(self.post.id,),
            ),
            data=form_data,
            follow=True,
        )
        modified_post = Post.objects.first()
        # проверка что кол-во постов не изменилось
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(modified_post.text, form_data['text'])
        self.assertEqual(modified_post.author, self.post.author)
        self.assertEqual(modified_post.group.pk, form_data['group'])
        self.assertRedirects(
            response,
            reverse(
                'posts:post_detail',
                args=(self.post.id,),
            ),
        )
        response = self.client.get(
            reverse('posts:group_posts', args=(self.group.slug,))
        )
        # Сделать запрос на старую группу, проверить что пришел код 200
        self.assertEqual(response.status_code, HTTPStatus.OK)
        page = response.context['page_obj']
        # Проверил что постов в группе 0.
        self.assertEqual(len(page.object_list), 0)
        # Сравнил id постов до и после
        self.assertEqual(modified_post.pk, self.post.pk)
