package main

import (
	"context"
	"log"
	"net"
	"sync"

	pb "translator/proto"

	"github.com/bregydoc/gtranslate"
	"golang.org/x/text/language"
	"google.golang.org/grpc"
)

// server はgRPCサーバーの実装を提供する構造体
type server struct {
	pb.UnimplementedTranslatorServer
}

// Translate は単一のテキストを翻訳するメソッド
// 引数:
//   - ctx: コンテキスト
//   - req: 翻訳リクエスト（原文、ソース言語、ターゲット言語を含む）
// 戻り値:
//   - *pb.TranslateResponse: 翻訳結果
//   - error: エラー情報
func (s *server) Translate(ctx context.Context, req *pb.TranslateRequest) (*pb.TranslateResponse, error) {
	// ソース言語をlanguage.Tag型に変換
	sourceLang, err := language.Parse(req.SourceLang)
	if err != nil {
		return nil, err
	}
	// ターゲット言語をlanguage.Tag型に変換
	targetLang, err := language.Parse(req.TargetLang)
	if err != nil {
		return nil, err
	}

	// gtranslateパッケージを使用して翻訳を実行
	result, err := gtranslate.Translate(req.Text, sourceLang, targetLang)
	if err != nil {
		return nil, err
	}
	return &pb.TranslateResponse{TranslatedText: result}, nil
}

// BatchTranslate は複数のテキストを並列で翻訳するメソッド
// 引数:
//   - ctx: コンテキスト
//   - req: バッチ翻訳リクエスト（複数の原文、ソース言語、ターゲット言語を含む）
// 戻り値:
//   - *pb.BatchTranslateResponse: 翻訳結果の配列
//   - error: エラー情報
func (s *server) BatchTranslate(ctx context.Context, req *pb.BatchTranslateRequest) (*pb.BatchTranslateResponse, error) {
	// ソース言語をlanguage.Tag型に変換
	sourceLang, err := language.Parse(req.SourceLang)
	if err != nil {
		return nil, err
	}
	// ターゲット言語をlanguage.Tag型に変換
	targetLang, err := language.Parse(req.TargetLang)
	if err != nil {
		return nil, err
	}

	// 並列処理のためのWaitGroupを初期化
	var wg sync.WaitGroup
	// 翻訳結果を格納する配列
	results := make([]string, len(req.Texts))
	// エラーを格納する配列
	errors := make([]error, len(req.Texts))

	// 各テキストに対して並列で翻訳を実行
	for i, text := range req.Texts {
		wg.Add(1)
		go func(idx int, t string) {
			defer wg.Done()
			result, err := gtranslate.Translate(t, sourceLang, targetLang)
			if err != nil {
				errors[idx] = err
				return
			}
			results[idx] = result
		}(i, text)
	}

	// すべての翻訳が完了するまで待機
	wg.Wait()

	// エラーチェック
	for _, err := range errors {
		if err != nil {
			return nil, err
		}
	}

	return &pb.BatchTranslateResponse{TranslatedTexts: results}, nil
}

// main はサーバーのエントリーポイント
// 50051ポートでgRPCサーバーを起動
func main() {
	// TCPリスナーを作成
	lis, err := net.Listen("tcp", ":50051")
	if err != nil {
		log.Fatalf("failed to listen: %v", err)
	}

	// gRPCサーバーを初期化
	s := grpc.NewServer()
	// 翻訳サービスを登録
	pb.RegisterTranslatorServer(s, &server{})
	
	// サーバーを起動
	log.Printf("server listening at %v", lis.Addr())
	if err := s.Serve(lis); err != nil {
		log.Fatalf("failed to serve: %v", err)
	}
} 