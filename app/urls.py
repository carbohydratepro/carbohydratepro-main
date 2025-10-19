from django.urls import path
from django.views.generic import RedirectView
from . import views
from rest_framework_simplejwt.views import TokenObtainPairView


urlpatterns = [
    path('', RedirectView.as_view(url='expenses/', permanent=True)),
    # path('top/', views.top, name='top'),
    # 支出管理
    path('expenses/', views.expenses_list, name='expense_list'),
    path('expenses/create/', views.create_expenses, name='create_expenses'),
    path('expenses/settings/', views.expenses_settings, name='expenses_settings'),
    path('expenses/edit/<int:transaction_id>/', views.edit_expenses, name='edit_expenses'),
    path('expenses/delete/<int:transaction_id>/', views.delete_expenses, name='delete_expenses'),
    # path('api/receive-data/', views.receive_data, name='receive_data'),
    # path('graph/', views.display_graph, name='display_graph'),
    # path('api/sensor-data/', views.get_sensor_data, name='get_sensor_data'),
    # path('video/varolant/', views.video_varolant, name='video_varolant'),
    # path('video/update/<int:post_id>/', views.update_video, name='update_video'),
    # path('video/delete/<int:post_id>/', views.delete_video, name='delete_video'),
    # path('video/comment/update/<int:comment_id>/', views.update_video_comment, name='update_video_comment'),
    # path('video/comment/delete/<int:comment_id>/', views.delete_video_comment, name='delete_video_comment'),
    # path('reorder/', views.ReorderView.as_view(), name='reorder'),
    # タスク管理
    path('tasks/', views.task_list, name='task_list'),
    path('tasks/create/', views.create_task, name='create_task'),
    path('tasks/edit/<int:task_id>/', views.edit_task, name='edit_task'),
    path('tasks/delete/<int:task_id>/', views.delete_task, name='delete_task'),
    # メモ管理
    path('memos/', views.memo_list, name='memo_list'),
    path('memos/create/', views.create_memo, name='create_memo'),
    path('memos/edit/<int:memo_id>/', views.edit_memo, name='edit_memo'),
    path('memos/delete/<int:memo_id>/', views.delete_memo, name='delete_memo'),
    path('memos/toggle-favorite/<int:memo_id>/', views.toggle_memo_favorite, name='toggle_memo_favorite'),
    # 買うものリスト
    path('shopping/', views.shopping_list, name='shopping_list'),
    path('shopping/create/', views.create_shopping_item, name='create_shopping_item'),
    path('shopping/edit/<int:item_id>/', views.edit_shopping_item, name='edit_shopping_item'),
    path('shopping/delete/<int:item_id>/', views.delete_shopping_item, name='delete_shopping_item'),
    path('shopping/update-count/<int:item_id>/', views.update_shopping_count, name='update_shopping_count'),
]