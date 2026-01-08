"""헬퍼 함수 테스트."""

from io import BytesIO

from src.utils.helpers import calculate_file_hash, validate_pdf_file


class TestCalculateFileHash:
    """calculate_file_hash 테스트 클래스."""

    def test_valid_file_content(self):
        """유효한 파일 콘텐츠에 대한 해시 계산."""
        content = b"Hello, World!"
        file = BytesIO(content)

        hash_result = calculate_file_hash(file)

        # SHA-256 해시는 64자 16진수 문자열
        assert isinstance(hash_result, str)
        assert len(hash_result) == 64
        assert all(c in "0123456789abcdef" for c in hash_result)

    def test_empty_file(self):
        """빈 파일에 대한 해시 계산."""
        empty_file = BytesIO(b"")

        hash_result = calculate_file_hash(empty_file)

        # 빈 문자열의 SHA-256 해시
        expected_hash = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        assert hash_result == expected_hash

    def test_same_content_same_hash(self):
        """동일한 콘텐츠는 동일한 해시 생성."""
        content = b"Test content for hashing"
        file1 = BytesIO(content)
        file2 = BytesIO(content)

        hash1 = calculate_file_hash(file1)
        hash2 = calculate_file_hash(file2)

        assert hash1 == hash2

    def test_different_content_different_hash(self):
        """다른 콘텐츠는 다른 해시 생성."""
        file1 = BytesIO(b"Content A")
        file2 = BytesIO(b"Content B")

        hash1 = calculate_file_hash(file1)
        hash2 = calculate_file_hash(file2)

        assert hash1 != hash2

    def test_file_position_reset(self):
        """해시 계산 후 파일 포인터가 처음으로 리셋되는지 확인."""
        content = b"Test content"
        file = BytesIO(content)

        # 파일 포인터를 중간으로 이동
        file.seek(5)

        calculate_file_hash(file)

        # 파일 포인터가 처음으로 리셋되었는지 확인
        assert file.tell() == 0

    def test_large_file_chunking(self):
        """큰 파일도 청크 단위로 처리."""
        # 8192 바이트보다 큰 파일 생성
        large_content = b"A" * 100000  # 100KB
        file = BytesIO(large_content)

        hash_result = calculate_file_hash(file)

        # 해시가 정상적으로 계산되어야 함
        assert isinstance(hash_result, str)
        assert len(hash_result) == 64

    def test_binary_content(self):
        """바이너리 콘텐츠도 정상 처리."""
        binary_content = bytes(range(256))  # 0x00 ~ 0xFF
        file = BytesIO(binary_content)

        hash_result = calculate_file_hash(file)

        assert isinstance(hash_result, str)
        assert len(hash_result) == 64


class TestValidatePDFFile:
    """validate_pdf_file 테스트 클래스."""

    def test_valid_pdf_with_magic_bytes(self):
        """유효한 PDF (매직 바이트 포함)."""
        pdf_content = b"%PDF-1.4\n" + b"\x00" * 1000
        file = BytesIO(pdf_content)

        is_valid, error = validate_pdf_file(file, "test.pdf", max_size_mb=50)

        assert is_valid is True
        assert error == ""
        # 파일 포인터가 처음으로 리셋되었는지 확인
        assert file.tell() == 0

    def test_valid_pdf_various_versions(self):
        """다양한 PDF 버전도 유효."""
        for version in ["1.0", "1.4", "1.7", "2.0"]:
            pdf_content = f"%PDF-{version}\n".encode() + b"\x00" * 1000
            file = BytesIO(pdf_content)

            is_valid, error = validate_pdf_file(file, "test.pdf", max_size_mb=50)

            assert is_valid is True
            assert error == ""

    def test_invalid_extension_txt(self):
        """잘못된 확장자 - .txt."""
        content = b"%PDF-1.4\n" + b"\x00" * 1000
        file = BytesIO(content)

        is_valid, error = validate_pdf_file(file, "test.txt", max_size_mb=50)

        assert is_valid is False
        assert "PDF 파일만 업로드 가능합니다." in error

    def test_invalid_extension_docx(self):
        """잘못된 확장자 - .docx."""
        content = b"%PDF-1.4\n" + b"\x00" * 1000
        file = BytesIO(content)

        is_valid, error = validate_pdf_file(file, "document.docx", max_size_mb=50)

        assert is_valid is False
        assert "PDF 파일만 업로드 가능합니다." in error

    def test_invalid_extension_no_extension(self):
        """확장자 없음."""
        content = b"%PDF-1.4\n" + b"\x00" * 1000
        file = BytesIO(content)

        is_valid, error = validate_pdf_file(file, "noextension", max_size_mb=50)

        assert is_valid is False
        assert "PDF 파일만 업로드 가능합니다." in error

    def test_file_too_large(self):
        """파일 크기 초과."""
        # 2MB 파일 생성 (PDF 매직 바이트 포함)
        large_content = b"%PDF-1.4" + b"\x00" * (2 * 1024 * 1024 - 8)
        file = BytesIO(large_content)

        is_valid, error = validate_pdf_file(file, "large.pdf", max_size_mb=1)

        assert is_valid is False
        assert "파일 크기가 1MB를 초과합니다." in error

    def test_file_at_size_limit(self):
        """파일 크기가 정확히 제한과 같을 때."""
        # 정확히 1MB (PDF 매직 바이트 포함)
        exact_size_content = b"%PDF-1.4" + b"\x00" * (1 * 1024 * 1024 - 8)
        file = BytesIO(exact_size_content)

        is_valid, error = validate_pdf_file(file, "exact.pdf", max_size_mb=1)

        assert is_valid is True
        assert error == ""

    def test_file_just_over_limit(self):
        """파일 크기가 제한을 1바이트 초과."""
        # 1MB + 1바이트 (PDF 매직 바이트 포함)
        over_limit_content = b"%PDF-1.4" + b"\x00" * (1 * 1024 * 1024 + 1 - 8)
        file = BytesIO(over_limit_content)

        is_valid, error = validate_pdf_file(file, "over.pdf", max_size_mb=1)

        assert is_valid is False
        assert "파일 크기가 1MB를 초과합니다." in error

    def test_empty_filename(self):
        """빈 파일명."""
        content = b"%PDF-1.4\n" + b"\x00" * 1000
        file = BytesIO(content)

        is_valid, error = validate_pdf_file(file, "", max_size_mb=50)

        assert is_valid is False
        assert "PDF 파일만 업로드 가능합니다." in error

    def test_case_insensitive_extension(self):
        """확장자 대소문자 구분 없음."""
        content = b"%PDF-1.4\n" + b"\x00" * 1000

        # 다양한 대소문자 조합
        filenames = ["test.PDF", "test.Pdf", "test.pDf", "test.pdF"]

        for filename in filenames:
            file = BytesIO(content)
            is_valid, error = validate_pdf_file(file, filename, max_size_mb=50)

            assert is_valid is True, f"Failed for {filename}"
            assert error == ""

    def test_filename_with_path(self):
        """경로가 포함된 파일명."""
        content = b"%PDF-1.4\n" + b"\x00" * 1000
        file = BytesIO(content)

        is_valid, error = validate_pdf_file(
            file, "/path/to/document.pdf", max_size_mb=50
        )

        assert is_valid is True
        assert error == ""

    def test_filename_with_spaces(self):
        """공백이 포함된 파일명."""
        content = b"%PDF-1.4\n" + b"\x00" * 1000
        file = BytesIO(content)

        is_valid, error = validate_pdf_file(
            file, "my document.pdf", max_size_mb=50
        )

        assert is_valid is True
        assert error == ""

    def test_filename_with_special_chars(self):
        """특수문자가 포함된 파일명."""
        content = b"%PDF-1.4\n" + b"\x00" * 1000
        file = BytesIO(content)

        is_valid, error = validate_pdf_file(
            file, "문서_2024-01-08.pdf", max_size_mb=50
        )

        assert is_valid is True
        assert error == ""

    def test_multiple_dots_in_filename(self):
        """파일명에 여러 개의 점이 있는 경우."""
        content = b"%PDF-1.4\n" + b"\x00" * 1000
        file = BytesIO(content)

        # 마지막 확장자가 .pdf면 유효
        is_valid, error = validate_pdf_file(
            file, "my.document.v1.0.pdf", max_size_mb=50
        )

        assert is_valid is True
        assert error == ""

    def test_zero_size_file(self):
        """크기가 0인 파일은 매직 바이트가 없으므로 실패."""
        empty_file = BytesIO(b"")

        is_valid, error = validate_pdf_file(empty_file, "empty.pdf", max_size_mb=50)

        assert is_valid is False
        assert "유효한 PDF 파일이 아닙니다" in error

    def test_different_size_limits(self):
        """다양한 크기 제한 테스트."""
        # PDF 매직 바이트 포함
        content = b"%PDF-1.4" + b"\x00" * (10 * 1024 * 1024 - 8)  # 10MB

        test_cases = [
            (5, False, "5MB"),   # 제한보다 큼
            (10, True, ""),      # 정확히 같음
            (20, True, ""),      # 제한보다 작음
        ]

        for max_size, expected_valid, expected_error_text in test_cases:
            file = BytesIO(content)
            is_valid, error = validate_pdf_file(file, "test.pdf", max_size_mb=max_size)

            assert is_valid == expected_valid
            if expected_error_text:
                assert expected_error_text in error
