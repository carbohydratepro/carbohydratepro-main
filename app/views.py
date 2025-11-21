from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Avg
from django.core.mail import send_mail
from django.conf import settings
from .forms import VideoPostForm, CommentForm, DateForm, ContactMessageForm
from .models import VideoPost, Comment, SensorData, ContactMessage
from datetime import datetime, timedelta
import json
import logging

from rest_framework.response import Response
from rest_framework.decorators import api_view
from .serializers import SensorDataSerializer
from django.http import JsonResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views import View

logger = logging.getLogger(__name__)

from .expenses.views import expenses_list, create_expenses, expenses_settings, edit_expenses, delete_expenses
from .memo.views import memo_list, create_memo, edit_memo, delete_memo, toggle_memo_favorite
from .shopping.views import shopping_list, create_shopping_item, edit_shopping_item, delete_shopping_item, update_shopping_count
from .task.views import task_list, create_task, edit_task, delete_task, get_day_tasks, task_settings

@api_view(["POST"])
def receive_data(request):
    serializer = SensorDataSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({"message": "Data saved successfully"}, status=201)
    return Response(serializer.errors, status=400)

def display_graph(request):
    form = DateForm(request.GET or None)
    return render(request, "app/sensor_graph.html", {"form": form})

@api_view(["GET"])
def get_sensor_data(request):
    selected_date = request.GET.get("date", None)
    if selected_date:
        date_obj = datetime.strptime(selected_date, "%Y-%m-%d")
        timestamps = [f"{hour}:00" for hour in range(24)]
        temperatures = []
        humidities = []
        illuminances = []

        for hour in range(24):
            start_time = datetime.combine(date_obj, datetime.min.time()) + timedelta(hours=hour)
            end_time = start_time + timedelta(hours=1)
            avg_data = SensorData.objects.filter(timestamp__range=(start_time, end_time)).aggregate(
                avg_temperature=Avg("temperature"),
                avg_humidity=Avg("humidity"),
                avg_illuminance=Avg("illuminance")
            )
            temperatures.append(avg_data["avg_temperature"] or 0)
            humidities.append(avg_data["avg_humidity"] or 0)
            illuminances.append(avg_data["avg_illuminance"] or 0)

        return Response({
            "timestamps": timestamps,
            "temperatures": temperatures,
            "humidities": humidities,
            "illuminance": illuminances
        })
    return Response({"error": "Invalid date"}, status=400)

@login_required
def video_varolant(request):
    form_error = {}
    search_word = request.GET.get("q", "")

    try:
        if request.method == "POST":
            try:
                data = json.loads(request.body)
            except json.JSONDecodeError:
                return JsonResponse({"success": False, "error": "リクエストデータ形式が不正です。"})

            if "date" in data:
                form = VideoPostForm(data)
                if form.is_valid():
                    post = form.save(commit=False)
                    post.user = request.user
                    post.save()
                    return JsonResponse({"success": True})
                else:
                    form_error = form.errors.get_json_data()
                    return JsonResponse({"success": False, "error": form_error})

            elif "comment_content" in data:
                post_id = data.get("post_id")
                comment_content = data.get("comment_content", "").strip()
                if post_id and comment_content:
                    post = get_object_or_404(VideoPost, id=post_id)
                    comment = Comment.objects.create(post=post, user=request.user, content=comment_content)
                    return JsonResponse({
                        "success": True,
                        "comment": {
                            "id": comment.id,
                            "content": comment.content,
                            "user": comment.user.username,
                            "created_at": comment.created_at.strftime("%Y-%m-%d %H:%M"),
                            "can_edit": (comment.user_id == request.user.id),
                        }
                    })
                else:
                    return JsonResponse({"success": False, "error": "コメント内容が必要です。"})

        posts = VideoPost.objects.prefetch_related("comments").order_by("-date")
        paginator = Paginator(posts, 100)

        if search_word:
            from django.db.models import Q
            posts = posts.filter(
                Q(title__icontains=search_word) |
                Q(character__icontains=search_word) |
                Q(notes__icontains=search_word) |
                Q(user__username__icontains=search_word) |
                Q(comments__content__icontains=search_word)
            ).distinct()

        for post in posts:
            if isinstance(post.date, str):
                post.date = datetime.strptime(post.date, "%Y-%m-%d")

        paginator = Paginator(posts, 100)
        page = request.GET.get("page", 1)
        try:
            posts_page = paginator.page(page)
        except PageNotAnInteger:
            posts_page = paginator.page(1)
        except EmptyPage:
            posts_page = paginator.page(paginator.num_pages)

        comment_form = CommentForm()
        return render(request, "app/video_varolant.html", {
            "form": VideoPostForm(),
            "posts": posts_page,
            "comment_form": comment_form,
            "form_error": form_error,
            "search_word": search_word,
        })
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})

@login_required
def update_video(request, post_id):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            post = get_object_or_404(VideoPost, id=post_id, user=request.user)
            try:
                date = datetime.strptime(data.get("date"), "%Y-%m-%d").date()
            except ValueError:
                return JsonResponse({"success": False, "error": json.dumps({"date": [{"message": "日付が不正です。"}]})})

            post.date = date
            result = data.get("result")
            if result not in ["win", "loss", "draw", "unknown"]:
                return JsonResponse({"success": False, "error": json.dumps({"result": [{"message": "勝敗の値が不正です。"}]})})

            post.title = data.get("title")
            post.character = data.get("character")
            post.video_url = data.get("video_url")
            post.notes = data.get("notes")
            post.full_clean()
            post.save()
            return JsonResponse({"success": True})
        except Exception as e:
            return JsonResponse({"success": False, "error": json.dumps({"error": [{"message": str(e)}]})})
    return JsonResponse({"success": False, "error": json.dumps({"error": [{"message": "無効なリクエストです。"}]})})

@login_required
def delete_video(request, post_id):
    post = get_object_or_404(VideoPost, id=post_id, user=request.user)
    post.delete()
    return JsonResponse({"success": True})

@login_required
def update_video_comment(request, comment_id):
    if request.method == "POST":
        comment = get_object_or_404(Comment, id=comment_id, user=request.user)
        comment.content = request.POST.get("content")
        comment.save()
        return JsonResponse({"success": True})
    return JsonResponse({"success": False})

@login_required
def delete_video_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id, user=request.user)
    comment.delete()
    return JsonResponse({"success": True})

class ReorderView(View):
    def get(self, request):
        return render(request, "app/reorder.html")

    def post(self, request):
        order_str = request.POST.get("order", "")
        new_order_ids = order_str.split(",")
        return redirect("reorder")

@login_required
def contact(request):
    if request.method == "POST":
        form = ContactMessageForm(request.POST)
        if form.is_valid():
            contact_message = form.save(commit=False)
            contact_message.user = request.user
            contact_message.save()
            
            try:
                inquiry_type_display = contact_message.get_inquiry_type_display()
                subject = f"【お問い合わせ】{inquiry_type_display}: {contact_message.subject}"
                message = f"""
新しいお問い合わせが届きました。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
【お問い合わせ情報】
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

種類: {inquiry_type_display}
件名: {contact_message.subject}
送信者: {request.user.email}
送信日時: {contact_message.created_at.strftime('%Y年%m月%d日 %H:%M:%S')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
【お問い合わせ内容】
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{contact_message.message}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

このメールは自動送信されています。
お問い合わせへの対応が完了したら、管理画面で「対応済み」にマークしてください。
"""
                admin_email = getattr(settings, "SECURITY_ALERT_EMAIL", "carbohydratepro@gmail.com")
                send_mail(subject=subject, message=message, from_email=settings.DEFAULT_FROM_EMAIL, recipient_list=[admin_email], fail_silently=False)
                messages.success(request, "お問い合わせを送信しました。ご連絡ありがとうございます。")
                logger.info(f"お問い合わせメール送信成功: {request.user.email} - {inquiry_type_display}")
            except Exception as e:
                logger.error(f"お問い合わせメール送信エラー: {str(e)}")
                messages.warning(request, "お問い合わせは保存されましたが、メール送信に失敗しました。")
            
            return redirect("contact")
        else:
            messages.error(request, "フォームに入力エラーがあります。")
    else:
        form = ContactMessageForm()
    
    user_messages = ContactMessage.objects.filter(user=request.user)[:10]
    context = {"form": form, "user_messages": user_messages}
    return render(request, "app/contact.html", context)