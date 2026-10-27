from django.contrib.staticfiles.storage import ManifestStaticFilesStorage


class ManifestStaticFilesStorageLax(ManifestStaticFilesStorage):
    """
    ManifestStaticFilesStorage のカスタム版。
    - manifest_strict=False: manifest 未登録時は保存先のファイルからハッシュを計算する
    - 保存先の実体が必要なため、テスト前にも collectstatic を実行する
    - DEBUG=True でもハッシュを付与する（デフォルトでは DEBUG 時はスキップされる）
    静的ファイルのURLにコンテンツハッシュを付与し、ブラウザキャッシュを自動無効化する。
    例: task.js → task.abc12345.js （collectstatic 後にハッシュが更新される）
    """
    manifest_strict = False

    def _url(self, hashed_name_func, name, force=False, hashed_files=None):
        # DEBUG モードでもハッシュを強制適用する
        return super()._url(hashed_name_func, name, force=True, hashed_files=hashed_files)
