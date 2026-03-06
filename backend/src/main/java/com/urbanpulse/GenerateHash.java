package com.urbanpulse;

import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;

public class GenerateHash {
    public static void main(String[] args) {
        System.out.println("======================================");
        System.out.println("HASH_OUTPUT=" + new BCryptPasswordEncoder().encode("test123"));
        System.out.println("======================================");
    }
}
