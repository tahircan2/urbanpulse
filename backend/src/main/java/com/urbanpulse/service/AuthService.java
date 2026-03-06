package com.urbanpulse.service;

import com.urbanpulse.dto.request.LoginRequest;
import com.urbanpulse.dto.request.RegisterRequest;
import com.urbanpulse.dto.response.AuthResponse;
import com.urbanpulse.entity.User;
import com.urbanpulse.repository.UserRepository;
import com.urbanpulse.security.JwtUtil;
import lombok.RequiredArgsConstructor;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@RequiredArgsConstructor
public class AuthService {

    private final UserRepository userRepository;
    private final PasswordEncoder passwordEncoder;
    private final AuthenticationManager authenticationManager;
    private final JwtUtil jwtUtil;
    private final UserDetailsService userDetailsService;

    @Transactional
    public AuthResponse register(RegisterRequest req) {
        if (userRepository.existsByEmail(req.getEmail().toLowerCase().trim())) {
            throw new IllegalArgumentException("Email already registered: " + req.getEmail());
        }
        User user = User.builder()
            .name(req.getName().trim())
            .email(req.getEmail().toLowerCase().trim())
            .passwordHash(passwordEncoder.encode(req.getPassword()))
            .role(req.getRole())
            .district(req.getDistrict())
            .enabled(true)
            .build();
        userRepository.save(user);

        UserDetails details = userDetailsService.loadUserByUsername(user.getEmail());
        String token = jwtUtil.generateToken(details);
        return buildResponse(user, token);
    }

    @Transactional(readOnly = true)
    public AuthResponse login(LoginRequest req) {
        // FIX: Added missing UsernameNotFoundException import
        // Authenticate first (throws BadCredentialsException on failure)
        authenticationManager.authenticate(
            new UsernamePasswordAuthenticationToken(
                req.getEmail().toLowerCase().trim(),
                req.getPassword()
            )
        );
        // Load user after successful auth
        User user = userRepository.findByEmail(req.getEmail().toLowerCase().trim())
            .orElseThrow(() -> new UsernameNotFoundException("User not found"));
        UserDetails details = userDetailsService.loadUserByUsername(user.getEmail());
        String token = jwtUtil.generateToken(details);
        return buildResponse(user, token);
    }

    private AuthResponse buildResponse(User user, String token) {
        return AuthResponse.builder()
            .token(token)
            .type("Bearer")
            .userId(user.getId())
            .name(user.getName())
            .email(user.getEmail())
            .role(user.getRole())
            .build();
    }
}
