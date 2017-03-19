package resource

import (
	"bytes"
	"path"
	"reflect"
	"testing"
)

var rootURI = path.Join("..", "testdata", "fs")

func TestOpenFSPackage(t *testing.T) {
	tests := []struct {
		name    string
		rootURI string
		wantErr bool
	}{
		{
			"open existing fs package",
			rootURI,
			false,
		},
		{
			"can't open non-existing fs package",
			rootURI + "not-exist",
			true,
		},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			pkg, err := OpenFSPackage(tt.rootURI)
			if (err != nil) != tt.wantErr {
				t.Errorf("OpenFSPackage(%v) error = %v, wantErr %v", tt.rootURI, err, tt.wantErr)
				return
			}
			if !tt.wantErr && pkg == nil {
				t.Errorf("OpenFSPackage(%v) = nil, want != nil", tt.rootURI)
			}
		})
	}
}

func TestFSPackage_Open(t *testing.T) {
	tests := []struct {
		name    string
		URI     string
		wantErr bool
	}{
		{
			"open directory Item inside package",
			"a",
			false,
		},
		{
			"open file Item inside package",
			"a/1/a1",
			false,
		},
		{
			"can't open non-existing Item inside package",
			"c",
			true,
		},
		{
			"can't open Item outside package(1)",
			"..",
			true,
		},
		{
			"can't open Item outside of a package(2)",
			"../fs/a/../../",
			true,
		},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			fs, err := OpenFSPackage(rootURI)
			got, err := fs.Open(tt.URI)
			if (err != nil) != tt.wantErr {
				t.Errorf("FSPackage.Open(%v) error = %v, wantErr %v", tt.URI, err, tt.wantErr)
				return
			}
			if !tt.wantErr && got == nil {
				t.Errorf("FSPackage.Open(%v) = nil, want != nil", tt.URI)
			}
		})
	}
}

func TestFSItem_Type(t *testing.T) {
	tests := []struct {
		name string
		URI  string
		want Type
	}{
		{
			"check directory type",
			"../fs/a",
			Directory,
		},
		{
			"check File type",
			"../fs/a/1/a1",
			File,
		},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			fs, _ := OpenFSPackage(rootURI)
			fsi, _ := fs.Open(tt.URI)
			got := fsi.Type()
			if got != tt.want {
				t.Errorf("URI(=%v) FSItem.Type() = %v, want %v", tt.URI, got, tt.want)
			}
		})
	}
}

func TestFSItem_Open(t *testing.T) {
	tests := []struct {
		name    string
		URI     string
		want    []byte
		wantErr bool
	}{
		{
			"can't read a directory item",
			"a",
			nil,
			true,
		},
		{
			"read a file item",
			"a/1/a1",
			[]byte("foo"),
			false,
		},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			fs, _ := OpenFSPackage(rootURI)
			fsi, _ := fs.Open(tt.URI)
			got, err := fsi.Open()
			if err == nil {
				defer got.Close()
			}
			if (err != nil) != tt.wantErr {
				t.Errorf("FSItem.Open() error = %v, wantErr %v", err, tt.wantErr)
				return
			}
			if got == nil {
				if tt.want != nil {
					t.Errorf("FSItem.Open() = nil, want %v", tt.want)
				}
			} else {
				// read
				var buf bytes.Buffer
				_, err = buf.ReadFrom(got)
				if !reflect.DeepEqual(buf.Bytes(), tt.want) {
					t.Errorf("FSItem.Open() read buf = %v, want %v", buf.Bytes(), tt.want)
				}
			}
		})
	}
}
