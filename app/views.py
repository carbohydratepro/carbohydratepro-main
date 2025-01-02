from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, F, Q, Avg
from django.utils.timezone import make_aware
from .forms import TransactionForm, PaymentMethodForm, CategoryForm, VideoPostForm, CommentForm
from .models import Transaction, PaymentMethod, Category, VideoPost, Comment
from datetime import datetime, timedelta

import json
import logging

from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .serializers import SensorDataSerializer
from .forms import DateForm
from .models import SensorData
from django.http import JsonResponse


logger = logging.getLogger(__name__)


@login_required
def index(request):
    target_date = request.GET.get('target_date', None)

    if target_date:
        target_date = make_aware(datetime.strptime(target_date, '%Y-%m'))
    else:
        # target_dateが指定されていない場合、現在の月をデフォルトとして設定
        target_date = make_aware(datetime.now().replace(day=1))

    start_date = target_date.replace(day=1)
    end_date = (start_date + timedelta(days=32)).replace(day=1) - timedelta(days=1)

    transactions = Transaction.objects.filter(user=request.user, date__range=(start_date, end_date))

    # 日付範囲の作成（固定された月初から月末）
    date_range = [(start_date + timedelta(days=i)).strftime('%Y-%m-%d') for i in range((end_date - start_date).days + 1)]

    # グラフ用データの作成
    category_data = transactions.values('category__name').annotate(total=Sum('amount')).order_by('-total')
    
    # メインカテゴリを日本語表記で取得
    major_category_data = transactions.values('major_category').annotate(total=Sum('amount')).order_by('-total')
    major_category_labels = {
        'variable': '変動費',
        'fixed': '固定費',
        'special': '特別費'
    }
    major_category_data_json = json.dumps({
        'labels': [major_category_labels[entry['major_category']] for entry in major_category_data],
        'datasets': [{
            'data': [float(entry['total']) for entry in major_category_data],  # Decimalをfloatに変換
            'backgroundColor': ['#4BC0C0', '#FF9F40', '#9966FF'],
        }]
    })

    expense_data = []
    balance_data = []
    current_balance = 0

    for date in date_range:
        daily_expense = transactions.filter(date__date=date, transaction_type='expense').aggregate(Sum('amount'))['amount__sum'] or 0
        daily_income = transactions.filter(date__date=date, transaction_type='income').aggregate(Sum('amount'))['amount__sum'] or 0
        current_balance += float(daily_income) - float(daily_expense)  # Decimalをfloatに変換
        expense_data.append(float(daily_expense))  # Decimalをfloatに変換
        balance_data.append(float(current_balance))  # Decimalをfloatに変換

    category_data_json = json.dumps({
        'labels': [entry['category__name'] for entry in category_data],
        'datasets': [{
            'data': [float(entry['total']) for entry in category_data],  # Decimalをfloatに変換
            'backgroundColor': ['#FF6384', '#36A2EB', '#FFCE56'],
        }]
    })

    expense_data_json = json.dumps({
        'labels': date_range,
        'datasets': [{
            'label': '支出',
            'data': expense_data,
            'backgroundColor': '#FF6384',
        }]
    })

    balance_data_json = json.dumps({
        'labels': date_range,
        'datasets': [{
            'label': '所持金',
            'data': balance_data,
            'fill': False,
            'borderColor': '#36A2EB',
        }]
    })

    return render(request, 'app/index.html', {
        'transactions': transactions,
        'category_data_json': category_data_json,
        'major_category_data_json': major_category_data_json,
        'expense_data_json': expense_data_json,
        'balance_data_json': balance_data_json,
        'default_target_date': target_date.strftime('%Y-%m')  # 今日の日付をテンプレートに渡す
    })
    
@login_required
def create_transaction(request):
    if request.method == 'POST':
        form = TransactionForm(request.POST, user=request.user)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.user = request.user
            transaction.save()
            return redirect('index')  # 投稿後は一覧画面にリダイレクト
    else:
        form = TransactionForm(user=request.user)
    return render(request, 'app/create_transaction.html', {'form': form})

@login_required
def settings_view(request):
    payment_limit = 10
    purpose_limit = 30

    payments = PaymentMethod.objects.filter(user=request.user)
    purposes = Category.objects.filter(user=request.user)

    payment_count = payments.count()
    purpose_count = purposes.count()

    payment_form = PaymentMethodForm(prefix='payment')
    purpose_form = CategoryForm(prefix='purpose')

    edit_payment_instance = None
    edit_purpose_instance = None

    if request.method == 'POST':
        if 'payment_id' in request.POST:
            payment = get_object_or_404(PaymentMethod, id=request.POST.get('payment_id'), user=request.user)
            if 'edit_payment' in request.POST:
                payment_form = PaymentMethodForm(request.POST, instance=payment, prefix='payment')
                if payment_form.is_valid():
                    payment_form.save()
                    return redirect('settings')
                edit_payment_instance = payment
            elif 'delete_payment' in request.POST:
                payment.delete()
                return redirect('settings')

        elif 'purpose_id' in request.POST:
            purpose = get_object_or_404(Category, id=request.POST.get('purpose_id'), user=request.user)
            if 'edit_purpose' in request.POST:
                purpose_form = CategoryForm(request.POST, instance=purpose, prefix='purpose')
                if purpose_form.is_valid():
                    purpose_form.save()
                    return redirect('settings')
                edit_purpose_instance = purpose
            elif 'delete_purpose' in request.POST:
                purpose.delete()
                return redirect('settings')

        else:
            if 'payment' in request.POST:
                payment_form = PaymentMethodForm(request.POST, prefix='payment')
                if payment_count >= payment_limit:
                    payment_form.add_error(None, f"支払方法の登録上限数は{payment_limit}件です。")
                elif payment_form.is_valid():
                    new_payment_method = payment_form.save(commit=False)
                    new_payment_method.user = request.user
                    new_payment_method.save()
                    return redirect('settings')

            elif 'purpose' in request.POST:
                purpose_form = CategoryForm(request.POST, prefix='purpose')
                if purpose_count >= purpose_limit:
                    purpose_form.add_error(None, f"使用用途の登録上限数は{purpose_limit}件です。")
                elif purpose_form.is_valid():
                    new_purpose = purpose_form.save(commit=False)
                    new_purpose.user = request.user
                    new_purpose.save()
                    return redirect('settings')

    return render(request, 'app/settings.html', {
        'payment_form': payment_form,
        'purpose_form': purpose_form,
        'payments': payments,
        'purposes': purposes,
        'edit_payment_instance': edit_payment_instance,
        'edit_purpose_instance': edit_purpose_instance,
    })

@login_required
def edit_transaction(request, transaction_id):
    transaction = get_object_or_404(Transaction, id=transaction_id, user=request.user)
    if request.method == 'POST':
        form = TransactionForm(request.POST, instance=transaction, user=request.user)
        if form.is_valid():
            form.save()
            return redirect('index')
    else:
        form = TransactionForm(instance=transaction, user=request.user)
    return render(request, 'app/edit_transaction.html', {'form': form})

@login_required
def delete_transaction(request, transaction_id):
    transaction = get_object_or_404(Transaction, id=transaction_id, user=request.user)
    if request.method == 'POST':
        transaction.delete()
        return redirect('index')
    return render(request, 'app/confirm_delete.html', {'transaction': transaction})

@api_view(['POST'])
def receive_data(request):
    serializer = SensorDataSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()  # 照度を含むデータを保存
        return Response({"message": "Data saved successfully"}, status=201)
    return Response(serializer.errors, status=400)


# グラフ表示用ビュー
def display_graph(request):
    form = DateForm(request.GET or None)
    return render(request, 'app/sensor_graph.html', {'form': form})

# 選択された日付に基づいてデータを取得するAPI
@api_view(['GET'])
def get_sensor_data(request):
    selected_date = request.GET.get('date', None)
    
    if selected_date:
        # 選択された日付に基づいてデータを取得
        date_obj = datetime.strptime(selected_date, '%Y-%m-%d')

        # 24時間分のデータを格納するリストを初期化
        timestamps = [f"{hour}:00" for hour in range(24)]
        temperatures = []
        humidities = []
        illuminances = []

        # 各時間帯ごとにデータを集計
        for hour in range(24):
            start_time = datetime.combine(date_obj, datetime.min.time()) + timedelta(hours=hour)
            end_time = start_time + timedelta(hours=1)

            # 各時間のデータの平均値を取得
            avg_data = SensorData.objects.filter(timestamp__range=(start_time, end_time)).aggregate(
                avg_temperature=Avg('temperature'),
                avg_humidity=Avg('humidity'),
                avg_illuminance=Avg('illuminance')
            )
            
            # 平均値をリストに追加 (Noneの場合は0にする)
            temperatures.append(avg_data['avg_temperature'] or 0)
            humidities.append(avg_data['avg_humidity'] or 0)
            illuminances.append(avg_data['avg_illuminance'] or 0)

        # 24時間分のデータをレスポンスに返す
        return Response({
            'timestamps': timestamps,
            'temperatures': temperatures,
            'humidities': humidities,
            'illuminance': illuminances
        })
    
    return Response({'error': 'Invalid date'}, status=400)



@login_required
def video_varolant(request):
    form_error = {}  # エラー変数の初期化

    try:
        # POSTリクエスト処理
        if request.method == 'POST':
            # JSONデータを解析
            try:
                data = json.loads(request.body)
            except json.JSONDecodeError:
                return JsonResponse({'success': False, 'error': 'リクエストデータ形式が不正です。'})

            # 新規投稿処理
            if 'date' in data:
                form = VideoPostForm(data)
                if form.is_valid():
                    post = form.save(commit=False)
                    post.user = request.user
                    post.save()
                    return JsonResponse({'success': True})
                else:
                    # フォームエラーを辞書形式で取得
                    form_error = form.errors.get_json_data()
                    return JsonResponse({'success': False, 'error': form_error})

            # コメント追加処理
            elif 'comment_content' in data:
                post_id = data.get('post_id')
                comment_content = data.get('comment_content', '').strip()
                if post_id and comment_content:
                    post = get_object_or_404(VideoPost, id=post_id)
                    Comment.objects.create(
                        post=post,
                        user=request.user,
                        content=comment_content
                    )
                    return JsonResponse({'success': True})
                else:
                    return JsonResponse({'success': False, 'error': 'コメント内容が必要です。'})

        # GETリクエスト処理
        posts = VideoPost.objects.prefetch_related('comments').order_by('-date')
        comment_form = CommentForm()

        # データレンダリング
        return render(request, 'app/video_varolant.html', {
            'form': VideoPostForm(),
            'posts': posts,
            'comment_form': comment_form,
            'form_error': form_error,
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def update_video(request, post_id):
    """投稿の編集処理 (JSON対応)"""
    if request.method == 'POST':
        try:
            # JSON形式でデータ受け取り
            data = json.loads(request.body)

            # データ取得
            post = get_object_or_404(VideoPost, id=post_id, user=request.user)

            # 日付形式変換
            try:
                date = datetime.strptime(data.get('date'), '%Y-%m-%d').date()
            except ValueError:
                return JsonResponse({'success': False, 'error': json.dumps({'date': [{'message': '日付はYYYY-MM-DD形式で指定してください。'}]})})

            # フィールド更新
            post.date = date
            logger.debug(post.date.strftime('%Y-%m-%d'))  # 出力確認

            result = data.get('result')
            if result not in ['win', 'loss', 'draw']:
                return JsonResponse({'success': False, 'error': json.dumps({'result': [{'message': '勝敗は正しい値を指定してください。'}]})})

            post.video_url = data.get('video_url')
            post.notes = data.get('notes')

            # バリデーションと保存
            post.full_clean()
            post.save()
            return JsonResponse({'success': True})

        except Exception as e:
            return JsonResponse({'success': False, 'error': json.dumps({'error': [{'message': str(e)}]})})
    return JsonResponse({'success': False, 'error': json.dumps({'error': [{'message': '無効なリクエストです。'}]})})

@login_required
def delete_video(request, post_id):
    """投稿の削除処理"""
    post = get_object_or_404(VideoPost, id=post_id, user=request.user)
    post.delete()
    return JsonResponse({'success': True})

@login_required
def update_video_comment(request, comment_id):
    """コメントの編集処理 (Ajax用)"""
    if request.method == 'POST':
        comment = get_object_or_404(Comment, id=comment_id, user=request.user)
        comment.content = request.POST.get('content')
        comment.save()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})

@login_required
def delete_video_comment(request, comment_id):
    """コメントの削除処理"""
    comment = get_object_or_404(Comment, id=comment_id, user=request.user)
    comment.delete()
    return JsonResponse({'success': True})