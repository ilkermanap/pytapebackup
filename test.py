import  unittest

from pytapebackup import MyAES, AESText

class TestMyAES(unittest.TestCase):
    def test_file_encrypt_decrypt(self):
        test_filename = "myaes_testfile.txt"
        test_output_filename = "myaes_testfile_output.txt"
        f = open(test_filename, "w")
        f.write("test content")
        f.close()

        encryptor = MyAES("test password")
        encryptor.encrypt(test_filename, remove_source=False)
        encryptor.decrypt(test_filename + ".enc", output_file="testout.txt")

        inf = open(test_filename, "rb")
        outf = open("testout.txt","rb")
        inp = inf.read()
        outp = outf.read()
        inf.close()
        outf.close()
        self.assertEqual(inp, outp)


class TestAESText(unittest.TestCase):
    def test_AESText_encrypt_decrypt(self):
        encryptor = AESText("test password")
        message = "Test Message"
        encrypted_text = encryptor.encrypt(message)
        decrypted_text = encryptor.decrypt(encrypted_text).decode()
        self.assertEqual(message, decrypted_text)

    
if __name__ == "__main__":
    unittest.main()
