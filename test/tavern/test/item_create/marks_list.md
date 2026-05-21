### テストの種類
|マーカー名                                  |説明|
|-------------------------------------------|---|
|item_create_author_db                      |著者DBに存在する著者と同じ著者情報を入力するアイテム個別登録テスト|
|item_create_author_not_match               |著者名が既存のアイテムと一致しないアイテム個別登録テスト|
|item_create_author_order_change            |既存のアイテムの著者と一致するが順番の異なるアイテム個別登録テスト|
|item_create_change_author_id               |アイテム個別登録中に著者DBのIDを変更するテスト|
|item_create_duplicate_doi_1                |DOIの重複が1件あるアイテム個別登録テスト|
|item_create_duplicate_doi_10               |DOIの重複が10件あるアイテム個別登録テスト|
|item_create_duplicate_doi_2                |DOIの重複が2件あるアイテム個別登録テスト|
|item_create_invalid_choice_case            |選択肢外の値を使用するアイテム個別登録テスト|
|item_create_no_duplicate                   |重複アイテムが存在しないアイテム個別登録|
|item_create_not_logged_in_case             |未ログイン状態でのアイテム個別登録テスト|
|item_create_registration_file              |ファイルを含むアイテム個別登録テスト|
|item_create_required_field_missing_case    |必須項目が未入力のアイテム個別登録テスト|
|item_create_resource_type_not_match        |資源タイプが既存のアイテムと一致しないアイテム個別登録テスト
|item_create_same_title_resource_type_author|タイトル、資源タイプ、著者が既存のアイテムと一致するアイテム個別登録テスト|
|item_create_success_case                   |アイテム個別登録の正常系テスト|
|item_create_title_not_match                |タイトルが既存のアイテムと一致しないアイテム個別登録テスト|
|item_create_title_variation                |タイトルが既存のアイテムとで表記ゆれが発生しているアイテム個別登録テスト|
|item_create_with_notification              |メール通知を含むアイテム個別登録|
