package main

import (
	"context"
	"log"
	"net"
	"sync"

	pb "translator/proto"

	"github.com/bregydoc/gtranslate"
	"google.golang.org/grpc"
)

type server struct {
	pb.UnimplementedTranslatorServer
}

func (s *server) Translate(ctx context.Context, req *pb.TranslateRequest) (*pb.TranslateResponse, error) {
	result, err := gtranslate.Translate(req.Text, req.SourceLang, req.TargetLang)
	if err != nil {
		return nil, err
	}
	return &pb.TranslateResponse{TranslatedText: result}, nil
}

func (s *server) BatchTranslate(ctx context.Context, req *pb.BatchTranslateRequest) (*pb.BatchTranslateResponse, error) {
	var wg sync.WaitGroup
	results := make([]string, len(req.Texts))
	errors := make([]error, len(req.Texts))

	for i, text := range req.Texts {
		wg.Add(1)
		go func(idx int, t string) {
			defer wg.Done()
			result, err := gtranslate.Translate(t, req.SourceLang, req.TargetLang)
			if err != nil {
				errors[idx] = err
				return
			}
			results[idx] = result
		}(i, text)
	}

	wg.Wait()

	// エラーチェック
	for _, err := range errors {
		if err != nil {
			return nil, err
		}
	}

	return &pb.BatchTranslateResponse{TranslatedTexts: results}, nil
}

func main() {
	lis, err := net.Listen("tcp", ":50051")
	if err != nil {
		log.Fatalf("failed to listen: %v", err)
	}

	s := grpc.NewServer()
	pb.RegisterTranslatorServer(s, &server{})
	
	log.Printf("server listening at %v", lis.Addr())
	if err := s.Serve(lis); err != nil {
		log.Fatalf("failed to serve: %v", err)
	}
} 