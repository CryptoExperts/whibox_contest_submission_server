#include <stdio.h>
#include <stdlib.h>

extern void AES_128_encrypt(unsigned char *ciphertext, unsigned char *plaintext);

int main() {
  void *plaintext = malloc(16);
  void *ciphertext = malloc(16);
  while (fread(plaintext, 1, 16, stdin) == 16) {
    AES_128_encrypt(ciphertext, plaintext);
    fwrite(ciphertext, 1, 16, stdout);
  }
  free(ciphertext);
  free(plaintext);
  return 0;
}
