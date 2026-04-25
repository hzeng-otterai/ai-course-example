import uuid

from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Notebook, Page, ShareLink


class AuthTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', email='test@example.com', password='password123'
        )

    def test_register_success(self):
        response = self.client.post('/api/auth/register/', {
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'password123',
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertEqual(response.data['user']['username'], 'newuser')

    def test_register_duplicate_username_returns_400(self):
        response = self.client.post('/api/auth/register/', {
            'username': 'testuser',
            'password': 'password123',
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_short_password_returns_400(self):
        response = self.client.post('/api/auth/register/', {
            'username': 'newuser2',
            'password': 'abc',
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_success(self):
        response = self.client.post('/api/auth/login/', {
            'username': 'testuser',
            'password': 'password123',
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_login_wrong_password_returns_401(self):
        response = self.client.post('/api/auth/login/', {
            'username': 'testuser',
            'password': 'wrongpassword',
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_returns_user_data(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/auth/me/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'testuser')
        self.assertEqual(response.data['email'], 'test@example.com')

    def test_me_unauthenticated_returns_401(self):
        response = self.client.get('/api/auth/me/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class NotebookTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='user1', password='password123')
        self.other = User.objects.create_user(username='user2', password='password123')
        self.notebook = Notebook.objects.create(user=self.user, title='My Notebook')

    def test_list_returns_only_own_notebooks(self):
        Notebook.objects.create(user=self.other, title='Other Notebook')
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/notebooks/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], 'My Notebook')

    def test_list_unauthenticated_returns_401(self):
        response = self.client.get('/api/notebooks/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_includes_page_count(self):
        Page.objects.create(notebook=self.notebook, title='P1')
        Page.objects.create(notebook=self.notebook, title='P2')
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/notebooks/')
        self.assertEqual(response.data[0]['page_count'], 2)

    def test_create_notebook(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post('/api/notebooks/', {'title': 'New Notebook'})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Notebook.objects.filter(user=self.user, title='New Notebook').exists())

    def test_retrieve_own_notebook(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f'/api/notebooks/{self.notebook.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'My Notebook')

    def test_retrieve_other_users_notebook_returns_404(self):
        self.client.force_authenticate(user=self.other)
        response = self.client.get(f'/api/notebooks/{self.notebook.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_own_notebook(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(f'/api/notebooks/{self.notebook.id}/', {'title': 'Updated'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.notebook.refresh_from_db()
        self.assertEqual(self.notebook.title, 'Updated')

    def test_update_other_users_notebook_returns_404(self):
        self.client.force_authenticate(user=self.other)
        response = self.client.patch(f'/api/notebooks/{self.notebook.id}/', {'title': 'Hacked'})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_own_notebook(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(f'/api/notebooks/{self.notebook.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Notebook.objects.filter(id=self.notebook.id).exists())

    def test_delete_other_users_notebook_returns_404(self):
        self.client.force_authenticate(user=self.other)
        response = self.client.delete(f'/api/notebooks/{self.notebook.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_notebook_detail_includes_nested_pages(self):
        Page.objects.create(notebook=self.notebook, title='Page 1')
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f'/api/notebooks/{self.notebook.id}/')
        self.assertEqual(len(response.data['pages']), 1)
        self.assertEqual(response.data['pages'][0]['title'], 'Page 1')


class PageTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='user1', password='password123')
        self.other = User.objects.create_user(username='user2', password='password123')
        self.notebook = Notebook.objects.create(user=self.user, title='My Notebook')
        self.other_notebook = Notebook.objects.create(user=self.other, title='Other Notebook')
        self.page = Page.objects.create(notebook=self.notebook, title='Page 1')

    def test_list_pages_in_own_notebook(self):
        Page.objects.create(notebook=self.notebook, title='Page 2')
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f'/api/notebooks/{self.notebook.id}/pages/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_list_pages_in_other_notebook_returns_404(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f'/api/notebooks/{self.other_notebook.id}/pages/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_page_assigns_sequential_order(self):
        Page.objects.create(notebook=self.notebook, title='Page 2', order=1)
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            f'/api/notebooks/{self.notebook.id}/pages/', {'title': 'Page 3'}
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['order'], 2)

    def test_create_page_in_other_notebook_returns_404(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            f'/api/notebooks/{self.other_notebook.id}/pages/', {'title': 'Hack'}
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_retrieve_own_page(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f'/api/pages/{self.page.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Page 1')

    def test_retrieve_other_users_page_returns_404(self):
        other_page = Page.objects.create(notebook=self.other_notebook, title='Other')
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f'/api/pages/{other_page.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_page_title_and_content(self):
        self.client.force_authenticate(user=self.user)
        content = {'type': 'doc', 'content': []}
        response = self.client.patch(
            f'/api/pages/{self.page.id}/',
            {'title': 'Updated', 'content': content},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.page.refresh_from_db()
        self.assertEqual(self.page.title, 'Updated')
        self.assertEqual(self.page.content, content)

    def test_update_other_users_page_returns_404(self):
        other_page = Page.objects.create(notebook=self.other_notebook, title='Other')
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(f'/api/pages/{other_page.id}/', {'title': 'Hacked'})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_own_page(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(f'/api/pages/{self.page.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Page.objects.filter(id=self.page.id).exists())

    def test_delete_other_users_page_returns_404(self):
        other_page = Page.objects.create(notebook=self.other_notebook, title='Other')
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(f'/api/pages/{other_page.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_page_content_defaults_to_empty_dict(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            f'/api/notebooks/{self.notebook.id}/pages/', {'title': 'Empty'}
        )
        self.assertEqual(response.data['content'], {})

    def test_share_token_is_null_by_default(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f'/api/pages/{self.page.id}/')
        self.assertIsNone(response.data['share_token'])


class ShareLinkTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='user1', password='password123')
        self.other = User.objects.create_user(username='user2', password='password123')
        self.notebook = Notebook.objects.create(user=self.user, title='My Notebook')
        self.page = Page.objects.create(notebook=self.notebook, title='My Page')

    def test_create_share_link(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(f'/api/pages/{self.page.id}/share/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)
        self.assertTrue(ShareLink.objects.filter(page=self.page, is_active=True).exists())

    def test_create_share_link_is_idempotent(self):
        self.client.force_authenticate(user=self.user)
        r1 = self.client.post(f'/api/pages/{self.page.id}/share/')
        r2 = self.client.post(f'/api/pages/{self.page.id}/share/')
        self.assertEqual(r1.data['token'], r2.data['token'])
        self.assertEqual(ShareLink.objects.filter(page=self.page, is_active=True).count(), 1)

    def test_revoke_share_link(self):
        ShareLink.objects.create(page=self.page, is_active=True)
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(f'/api/pages/{self.page.id}/share/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(ShareLink.objects.filter(page=self.page, is_active=True).exists())

    def test_create_share_for_other_users_page_returns_404(self):
        other_notebook = Notebook.objects.create(user=self.other, title='Other')
        other_page = Page.objects.create(notebook=other_notebook, title='Other Page')
        self.client.force_authenticate(user=self.user)
        response = self.client.post(f'/api/pages/{other_page.id}/share/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_public_shared_page_returns_content(self):
        link = ShareLink.objects.create(page=self.page, is_active=True)
        response = self.client.get(f'/api/shared/{link.token}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'My Page')
        self.assertEqual(response.data['notebook_title'], 'My Notebook')

    def test_public_shared_page_requires_no_auth(self):
        link = ShareLink.objects.create(page=self.page, is_active=True)
        response = self.client.get(f'/api/shared/{link.token}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_inactive_share_link_returns_404(self):
        link = ShareLink.objects.create(page=self.page, is_active=False)
        response = self.client.get(f'/api/shared/{link.token}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_invalid_share_token_returns_404(self):
        response = self.client.get(f'/api/shared/{uuid.uuid4()}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_page_serializer_shows_active_share_token(self):
        link = ShareLink.objects.create(page=self.page, is_active=True)
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f'/api/pages/{self.page.id}/')
        self.assertEqual(response.data['share_token'], str(link.token))

    def test_revoked_link_becomes_inaccessible(self):
        link = ShareLink.objects.create(page=self.page, is_active=True)
        self.client.force_authenticate(user=self.user)
        self.client.delete(f'/api/pages/{self.page.id}/share/')
        response = self.client.get(f'/api/shared/{link.token}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_page_serializer_shows_null_share_token_after_revoke(self):
        ShareLink.objects.create(page=self.page, is_active=True)
        self.client.force_authenticate(user=self.user)
        self.client.delete(f'/api/pages/{self.page.id}/share/')
        response = self.client.get(f'/api/pages/{self.page.id}/')
        self.assertIsNone(response.data['share_token'])
