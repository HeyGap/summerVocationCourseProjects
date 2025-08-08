#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include "sm4.h"
#include "utils.h"

void test_gcm_mode() {
    printf("Testing SM4-GCM mode...\n");

    const unsigned char key[16] = {
        0x01, 0x23, 0x45, 0x67, 0x89, 0xab, 0xcd, 0xef,
        0xfe, 0xdc, 0xba, 0x98, 0x76, 0x54, 0x32, 0x10
    };
    const unsigned char iv[12] = {
        0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07,
        0x08, 0x09, 0x0a, 0x0b
    };
    const unsigned char plaintext[32] = "This is a test for SM4-GCM mode";
    unsigned char ciphertext[32];
    unsigned char decrypted[32];
    unsigned char tag[16];

    gcm_context ctx;

    // Encrypt
    sm4_gcm_init(&ctx, key);
    sm4_gcm_crypt(&ctx, 1, 32, iv, plaintext, ciphertext);
    sm4_gcm_finish(&ctx, tag, 16);

    // Decrypt
    sm4_gcm_init(&ctx, key);
    sm4_gcm_crypt(&ctx, 0, 32, iv, ciphertext, decrypted);
    
    if (memcmp(plaintext, decrypted, 32) == 0) {
        printf("  PASS: GCM mode encryption and decryption successful.\n");
    } else {
        printf("  FAIL: GCM mode decryption does not match plaintext.\n");
    }
}

int main() {
    test_gcm_mode();
    return 0;
}
