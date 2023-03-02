from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from ..forms import PostForm
from ..models import Group, Post

User = get_user_model()


class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
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
            text='Тестовый пост нумер ван',
            group=cls.group
        )
        cls.form = PostForm()

    def test_create_post_authorized(self):
        post_count = Post.objects.count()
        form_data = {
            'group': self.group.id,
            'text': 'Тестовый текст',
        }
        response = self.author_client.post(
            reverse('posts:post_create'),
            data=form_data
        )
        self.assertRedirects(
            response,
            reverse(
                'posts:profile',
                kwargs={'username': self.author.username},
            ),
        )
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertTrue(
            Post.objects.filter(
                author=self.author,
                group=self.group,
                text='Тестовый текст',
            ).exists()
        )


class PostEditFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='author')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)

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
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый пост нумер ван',
            group=cls.group
        )
        cls.form = PostForm(instance=cls.post)

    def test_edit_post_authorized(self):
        posts_count = Post.objects.count()
        form_data = {
            'group': self.group_new.id,
            'text': 'Отредактированный пост',
        }
        response = self.author_client.post(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': self.post.id},
            ),
            data=form_data,
            follow=True,
        )
        modified_post = Post.objects.get(id=self.post.id)
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(modified_post.text, 'Отредактированный пост')
        self.assertEqual(modified_post.group, self.group_new)
        self.assertRedirects(
            response,
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.id},
            ),
        )
