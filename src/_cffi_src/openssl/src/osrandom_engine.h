#ifdef _WIN32
  #include <Wincrypt.h>
#else
  #include <fcntl.h>
  #include <unistd.h>
   /* for defined(BSD) */
  #include <sys/param.h>

  #ifdef BSD
    /* for SYS_getentropy */
    #include <sys/syscall.h>
  #endif

  #ifdef __linux__
    /* for SYS_getrandom */
    #include <sys/syscall.h>
    #ifndef GRND_NONBLOCK
      #define GRND_NONBLOCK 0x0001
    #endif /* GRND_NONBLOCK */
  #endif /* _linux__ */

  #ifdef __APPLE__
    #include <AvailabilityMacros.h>
    /* #if defined(MAC_OS_X_VERSION_10_10) || MAC_OS_X_VERSION_MIN_REQUIRED >= MAC_OS_X_VERSION_10_10 */
    #ifdef __MAC_10_10
      #include <CommonCrypto/CommonCryptor.h>
      #include <CommonCrypto/CommonRandom.h>
      #ifndef CRYPTOGRAPHY_HAVE_COMMON_RANDOM_H
        #define CRYPTOGRAPHY_HAVE_COMMON_RANDOM_H 1
      #endif
    #endif /* >= 10.10 */
  #endif /* __APPLE__ */
#endif /* _WIN32 */

#define CRYPTOGRAPHY_OSRANDOM_ENGINE_CRYPTGENRANDOM 1
#define CRYPTOGRAPHY_OSRANDOM_ENGINE_CC_RANDOM 2
#define CRYPTOGRAPHY_OSRANDOM_ENGINE_GETENTROPY 3
#define CRYPTOGRAPHY_OSRANDOM_ENGINE_GETRANDOM 4
#define CRYPTOGRAPHY_OSRANDOM_ENGINE_DEV_URANDOM 5

/* getentropy is not available in FreeBSD-10.1-RELEASE-p5 and older
 * TODO: check NetBSD and Darwin */
#if defined(_WIN32)
  /* Windows */
  #define CRYPTOGRAPHY_OSRANDOM_ENGINE CRYPTOGRAPHY_OSRANDOM_ENGINE_CRYPTGENRANDOM
#elif defined(__APPLE__) && defined(CRYPTOGRAPHY_HAVE_COMMON_RANDOM_H)
  /* OSX 10.10+ */
  #define CRYPTOGRAPHY_OSRANDOM_ENGINE CRYPTOGRAPHY_OSRANDOM_ENGINE_CC_RANDOM
#elif defined(BSD) && defined(SYS_getentropy)
  /* OpenBSD 5.6+ */
  #define CRYPTOGRAPHY_OSRANDOM_ENGINE CRYPTOGRAPHY_OSRANDOM_ENGINE_GETRANDOM
#elif defined(__linux__) && defined(SYS_getrandom)
  /* Linux 3.4.17+ */
  #define CRYPTOGRAPHY_OSRANDOM_ENGINE CRYPTOGRAPHY_OSRANDOM_ENGINE_GETENTROPY
  #define CRYPTOGRAPHY_OSRANDOM_NEEDS_DEV_URANDOM 1
#endif

/* Fall back to /dev/urandom */
#ifndef CRYPTOGRAPHY_OSRANDOM_ENGINE
  #define CRYPTOGRAPHY_OSRANDOM_ENGINE CRYPTOGRAPHY_OSRANDOM_ENGINE_DEV_URANDOM
  #define CRYPTOGRAPHY_OSRANDOM_NEEDS_DEV_URANDOM 1
#endif

/* Open SSL 1.1.0+ has no ERR_R_RAND_LIB */
#ifdef ERR_R_RAND_LIB
  #define CRYPTOGRAPHY_OSRANDOM_put_error(funcname) \
      ERR_put_error(ERR_LIB_RAND, 0, ERR_R_RAND_LIB, funcname, 0)
#else
  #define CRYPTOGRAPHY_OSRANDOM_put_error(funcname) \
      ERR_put_error(ERR_LIB_RAND, 0, 0, funcname, 0)
#endif