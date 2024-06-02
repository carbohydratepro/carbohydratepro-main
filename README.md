# 自分用のプロジェクト

## 開発
Docker-Desktopを使用したDjangoアプリケーション作成手順

### 1. プロジェクト立ち上げ

#### 前提条件
* Docker Desktopがインストールされていること
* GitHubがインストールされていること
* Visual Studio Codeがインストールされていること

#### 1-1. Djangoプロジェクト作成
```text
django-admin startproject ディレクトリ名
```

#### 1-2. 仮想環境立ち上げ
プロジェクト内にDockerfileを作成し、内容を記述

---

### 1. 開発環境時コマンド
```text
docker-compose -f docker-compose-dev.yml [down, build, up, exec...]
```

### 2. 本番環境時コマンド
```text
docker-compose [down, build, up, exec...]
```

### 3. 本番環境セットアップ
接続
```text
ssh -i [sshkey] username@ip
```
環境セットアップ
```linux
sudo yum update -y
sudo amazon-linux-extras install docker
sudo service docker start
sudo usermod -a -G docker ec2-user

sudo curl -L "https://github.com/docker/compose/releases/download/v2.11.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

sudo yum install git -y
git clone [project URL]
```



### 101. メンテナンスモード及び実行


### 999. コマンド


### 1000. デプロイ

```

### 使用技術
   | 要素 | 名称 | バージョン |
   |---|---|---|
   | フレームワーク | Django | 3.2 |
   | 言語 | Python | 3.9 |
   | 言語 | JavaScript |  |
   | 言語 | HTML&CSS |  |
   | ライブラリ | Bootstrap |  |
   | データベース | PostgeSQL | 13 |
   | クラウド/インフラ | DockerDesktop |  |
   | クラウド/インフラ | Amazon lightsail |  |
   | サーバー | Nginx | 1.17.7 |
   | サーバー | Gunicorn | 20.1.0 |
   
### 参考
###### AWS LightSailへのRemote-SSH接続
https://qiita.com/AsazuTaiga/items/6f1ba65897ddaf7b48b4
