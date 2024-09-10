# RepoTimelapse
# RepoTimelapse

RepoTimelapseは、GitリポジトリのタイムラインをLOC（行数）の変化に基づいて視覚化するツールです。このREADMEでは、Dockerを使用してRepoTimelapseをセットアップし、実行する方法を説明します。

## 前提条件

- Docker
- Docker Compose（オプション、ただし推奨）

## セットアップ

1. このリポジトリをクローンします：
   ```
   git clone https://github.com/yourusername/RepoTimelapse.git
   cd RepoTimelapse
   ```

2. Dockerイメージをビルドします：
   ```
   docker build -t repotimelapse .
   ```

## 実行方法

RepoTimelapseは、コマンドライン引数を使用するか、対話的に実行することができます。

### コマンドライン引数を使用する場合：

```
docker run --rm -v $(pwd)/output:/app/output repotimelapse --repo_url https://github.com/username/repo.git --extensions .java .kt .xml
```

- `--repo_url`: 分析するGitリポジトリのURL
- `--extensions`: 分析対象のファイル拡張子（スペース区切りで複数指定可能）

### 対話的に実行する場合：

```
docker run -it --rm -v $(pwd)/output:/app/output repotimelapse
```

プロンプトが表示されたら、分析するリポジトリのURLを入力してください。

### 注意事項：

- `-v $(pwd)/output:/app/output`: このオプションにより、分析結果がホストマシンの`out`ディレクトリに保存されます。
- `--rm`: コンテナを使い捨てモードで実行します（実行後に自動的に削除されます）。

## Docker Composeを使用する場合（オプション）

1. `docker-compose.yml`ファイルがプロジェクトルートにあることを確認します。

2. 以下のコマンドで実行します：
   ```
   docker-compose run --rm app --repo_url https://github.com/username/repo.git
   ```
   または、対話的に実行する場合：
   ```
   docker-compose run --rm app
   ```

## 出力

分析結果は、ホストマシンの`out`ディレクトリに保存されます。結果には、LOCの変化を示すグラフやその他の視覚化データが含まれます。
