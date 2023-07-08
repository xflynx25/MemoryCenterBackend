from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from django.urls import reverse
from .models import CollectionTable, TopicTable, ItemTable, UserItem, CustomUser
import json
from urllib.parse import urlencode
import time  

def print_success(testname):
    print('==============================================')
    print(f'Test for {testname} passed successfully.')
    print('==============================================')

class FlashcardsTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.user1 = CustomUser.objects.create_user(
            username="user1",
            password="password",
            realname="User One",
            description="User One description",
            awards="Award1, Award2"
        )
        self.user2 = CustomUser.objects.create_user(
            username="user2",
            password="password",
            realname="User Two",
            description="User Two description",
            awards="Award3, Award4"
        )
        self.user3 = CustomUser.objects.create_user(
            username="user3",
            password="password",
            realname="User Three",
        )



    def json_post_req(self, endpoint, data):
        return self.client.post(reverse(endpoint), data=json.dumps(data), content_type='application/json')
    
    def json_get_req(self, endpoint, data = None): 
        if data:
            return self.client.get(reverse(endpoint) + '?' + urlencode(data))
        else: 
            return self.client.get(reverse(endpoint)) 
        
    def url_get_req(self, endpoint, data=None):
        if data: 
            return self.client.get(reverse(endpoint, kwargs=data))
        else: 
            return self.client.get(reverse(endpoint))

    
    # HELPER FUNCTION: also sets the cookie 
    def login_user_for_tests(self, username, password):    
        # clear existing Authorization header if possible, aka log out
        self.client.credentials(HTTP_AUTHORIZATION='')  # Correct way to clear the credentials

        # login
        response = self.json_post_req('login',{'username': username, 'password': password})
        #response = self.client.post(reverse('login'), data={'username': username, 'password': password})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'success')
        # add access token to Authorization header
        token = response.json()['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        # return
        return response 
    

    # 1. (AUTHENTICATION) Simple Registration
    def Ttest_authentication(self):
        print("Testing authentication...")

        response = self.json_post_req('register', {'username': 'testuser', 'password': 'testpass'})
        self.assertEqual(response.status_code, 201)
        print_success("authentication")

    # 2. (PROFILES) Register two users, view own profile, make update, have other person view first profile
    def Ttest_profiles(self):
        print("Testing profiles...")

        # login
        response = self.login_user_for_tests('user1', 'password')
        self.assertEqual(response.json()['status'], 'success')
        
        # view own profile
        response = self.json_get_req('view_profile')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['username'], 'user1')
        
        # update profile
        response = self.json_post_req('edit_profile',{"description": "New description"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['description'], 'New description')
        
        # other person view first profile
        response = self.login_user_for_tests('user2', 'password')
        response = self.url_get_req('view_profile', {'user_id': self.user1.id})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['description'], 'New description')
        print_success("profiles")

    # 3. (DATA SETUP) Register user, make collection, make three topics, add two to collection, remove one from collection, add items. Then check all items in collection
    def Ttest_data_setup(self):
        print("Testing data setup...")

        self.login_user_for_tests('user1', 'password')
        
        # create collection
        response = self.json_post_req('create_collection', {'collection_name': 'Collection1'})
        self.assertEqual(response.status_code, 201)
        collection_id = response.json()['id']
        
        # create three topics, and add 3 + i items to each of them 
        for i in range(3):
            response = self.json_post_req('create_topic',{'topic_name': f'Topic{i + 1}'})
            self.assertEqual(response.status_code, 201)
            topic_id = response.json()['id']
            
            # add items to topic
            items_to_add = [[f'front{j + 1}', f'back{j + 1}'] for j in range(3+i)]
            response = self.json_post_req('add_items_to_topic', {'topic_id': topic_id, 'items': items_to_add})
            self.assertEqual(response.status_code, 200)
            
            if i > 0:
                # add two topics to collection
                response = self.json_post_req('edit_topics_in_collection',{'collection_id': collection_id, 'topic_edits': [[topic_id, 'add']]})
                self.assertEqual(response.status_code, 200)

        # verify number of topics
        response = self.json_get_req('get_all_collections')
        print('\ninitial collections = ', response.json())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(len(response.json()[0]['topics']), 2)
        
        # fetch all items from collection
        response = self.json_get_req('fetch_n_from_collection', {'collection_id': collection_id, 'n': 100})
        self.assertEqual(response.status_code, 200)
        items_count_before = len(response.json())

        # remove one topic from collection
        response = self.json_post_req('edit_topics_in_collection',{'collection_id': collection_id, 'topic_edits': [[topic_id, 'delete']]})
        self.assertEqual(response.status_code, 200)
        
        # verify number of topics
        response = self.url_get_req('get_all_collections')
        print('\nfinal collections = ', response.json())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(len(response.json()[0]['topics']), 1)
        
        # fetch all items from collection
        response = self.json_get_req('fetch_n_from_collection',{'collection_id': collection_id, 'n': 100})
        self.assertEqual(response.status_code, 200)
        items_count_after = len(response.json())

        self.assertLess(items_count_after, items_count_before)
        print_success("data setup")

        
    
    # 4. (STUDYING) Register user, make collection, make two topics, disactivate one, make some items, alternate between fetching n and updating
    # still would want to check for going out of the bounds with the score 
    def Ttest_studying(self):
        print("Testing studying...")
        num_items_total = 5
        fetch_size = 3
        num_fetches = 5

        self.login_user_for_tests('user1', 'password')
        
        # create collection
        response = self.json_post_req('create_collection',{'collection_name': 'Collection1'})
        self.assertEqual(response.status_code, 201)
        collection_id = response.json()['id']
        
        # create two topics
        topic_ids = []
        for i in range(2):
            response = self.json_post_req('create_topic',{'topic_name': f'Topic{i + 1}'})
            self.assertEqual(response.status_code, 201)
            topic_ids.append(response.json()['id'])
            # add two topics to collection
            response = self.json_post_req('edit_topics_in_collection',{'collection_id': collection_id, 'topic_edits': [[response.json()['id'], 'add']]})
            self.assertEqual(response.status_code, 200)
        
        # deactivate one topic
        response = self.json_post_req('edit_topics_in_collection',{'collection_id': collection_id, 'topic_edits': [[topic_ids[0], 'update']]})
        self.assertEqual(response.status_code, 200)

        # create some items
        for i in range(num_items_total):
            response = self.json_post_req('add_items_to_topic',{'topic_id': topic_ids[1], 'items': [[f'front{i + 1}', f'back{i + 1}']]})
            self.assertEqual(response.status_code, 200)

        # alternate between fetching n and updating
        for _ in range(num_fetches):  # change this value as per your requirements
            # fetch 5 items from collection
            response = self.json_get_req('fetch_n_from_collection', {'collection_id': collection_id, 'n': fetch_size})
            self.assertEqual(response.status_code, 200)
            
            items_data = [{'item_id': item['id'], 'increment': 1} for item in response.json()]
            
            # update fetched items
            response = self.json_post_req('update_n_items_user',{'items': items_data})
            self.assertEqual(response.status_code, 200)

        # visualize the final scoring
        response = self.json_get_req('fetch_n_from_collection',{'collection_id': collection_id, 'n': num_items_total})
            
        # some sort of check that the order is correct
        min_fetches = num_fetches*fetch_size // num_items_total
        for item in response.json():
            self.assertLess(min_fetches - 1, item['score']) 
        print('final score list = ', response.json()) # just for visualis

        print_success("studying")


    # 5. (GLOBAL VIEWING) register three users, make topics with each of them, 
    # user 1 wants to view from other two. user 2 sets to global 'view', user 3 sets to private. 
    # Then, have uesr3 set to 'global_edit', and have user1 try to add items to both 2 and 3's topics. 
    def test_global_viewing(self):
        print("Testing global viewing...")
        self.login_user_for_tests('user1', 'password')

        # create users and topics
        users = ['user1', 'user2', 'user3']
        topics = ['Topic1', 'Topic2', 'Topic3']
        visibilities = ['private', 'global_view', 'private']
        for user, topic, visibility in zip(users, topics, visibilities):
            self.login_user_for_tests(user, 'password')
            response = self.json_post_req('create_topic',{'topic_name': topic, 'visibility':visibility})
            self.assertEqual(response.status_code, 201)

        # user1 tries to view user2's topic (should be successful)
        self.login_user_for_tests('user1', 'password')
        response = self.url_get_req('get_all_topics', {'user_id': self.user2.id})
        print(response.json())
        self.assertEqual(response.status_code, 200)
        self.assertTrue(len(response.json()) >= 1)  # topic list should not be empty

        # user1 tries to view user3's topic (should return an empty list)
        response = self.url_get_req('get_all_topics', {'user_id': self.user3.id})
        print(response.json())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 0)  # topic list should be empty

        # user3 sets visibility to global 'edit'
        self.login_user_for_tests('user3', 'password')
        response = self.json_post_req('edit_topic_info',{'topic_id':3, 'edits': {'visibility': 'global_edit'}})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(len(response.json()) >= 1)  # topic list should not be empty

        # user1 tries to add items to user2's topic (should be unsuccessful)
        self.login_user_for_tests('user1', 'password')
        response = self.json_post_req('add_items_to_topic',{'topic_id': 2, 'items': [['front1', 'back1']]})
        self.assertEqual(response.status_code, 401)

        # user1 tries to add items to user3's topic (should be successful)
        response = self.json_post_req('add_items_to_topic',{'topic_id': 3, 'items': [['front1', 'back1']]})
        self.assertEqual(response.status_code, 200)

        # ADDITION: view the updated topic with the added items
        self.login_user_for_tests('user3', 'password')
        response = self.url_get_req('get_all_items')
        print("Updated items in topic:", response.json())
        self.assertEqual(response.status_code, 200)
        self.assertTrue(len(response.json()) >= 1) # failing because does not by default create the new card for all users with access. So only 1 is getting the new card

        print_success("global viewing")





    # 6. (FETCH TIMING) register user, set up three topics, add 25 items to one, 400 to another, and 10000 to another. Add each to different collections, and run the fetch_n. See difference in timings. 
    def Ttest_fetch_timing(self):
        print("Testing fetch timing...")
        self.login_user_for_tests('user1', 'password')

        # create topics and add items
        topic_ids = []
        num_items = [25, 400, 10000]
        for i, num_item in enumerate(num_items):
            # create topic
            response = self.json_post_req('create_topic',{'topic_name': f'Topic{i + 1}'})
            self.assertEqual(response.status_code, 201)
            topic_id = response.json()['id']
            topic_ids.append(topic_id)

            # add items to topic
            items = [[f'front{j + 1}', f'back{j + 1}'] for j in range(num_item)]
            response = self.json_post_req('add_items_to_topic',{'topic_id': topic_id, 'items': items})
            self.assertEqual(response.status_code, 200)

        # measure fetch timings
        for topic_id in topic_ids:
            start_time = time.time()
            response = self.json_get_req('fetch_n_from_collection', {'collection_id': topic_id, 'n': 10})
            end_time = time.time()
            print(f"Fetch time for topic {topic_id}: {end_time - start_time} seconds")

        print_success("fetch timing")

    # 7. (TOKENS) register user, try using the update token endpoint, and make sure you can still access edit_profile(self) endpoint
    def Ttest_tokens(self):
        print("Testing tokens...")
        response = self.login_user_for_tests('user1', 'password')
        old_token = self.client._credentials['HTTP_AUTHORIZATION']

        # get refresh token from login response
        refresh_token = response.json()["refresh"]

        # get new access token
        response = self.client.post(reverse('token_refresh'), data={'refresh': refresh_token})
        self.assertEqual(response.status_code, 200)

        # set new access token
        new_token = 'Bearer ' + response.json()["access"]
        self.client.credentials(HTTP_AUTHORIZATION=new_token)

        # try accessing protected route
        response = self.json_post_req('edit_profile',{'realname': 'New Name'})
        self.assertEqual(response.status_code, 200)
        print_success("tokens")

