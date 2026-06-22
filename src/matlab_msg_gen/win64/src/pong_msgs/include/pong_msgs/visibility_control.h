#ifndef PONG_MSGS__VISIBILITY_CONTROL_H_
#define PONG_MSGS__VISIBILITY_CONTROL_H_
#if defined _WIN32 || defined __CYGWIN__
  #ifdef __GNUC__
    #define PONG_MSGS_EXPORT __attribute__ ((dllexport))
    #define PONG_MSGS_IMPORT __attribute__ ((dllimport))
  #else
    #define PONG_MSGS_EXPORT __declspec(dllexport)
    #define PONG_MSGS_IMPORT __declspec(dllimport)
  #endif
  #ifdef PONG_MSGS_BUILDING_LIBRARY
    #define PONG_MSGS_PUBLIC PONG_MSGS_EXPORT
  #else
    #define PONG_MSGS_PUBLIC PONG_MSGS_IMPORT
  #endif
  #define PONG_MSGS_PUBLIC_TYPE PONG_MSGS_PUBLIC
  #define PONG_MSGS_LOCAL
#else
  #define PONG_MSGS_EXPORT __attribute__ ((visibility("default")))
  #define PONG_MSGS_IMPORT
  #if __GNUC__ >= 4
    #define PONG_MSGS_PUBLIC __attribute__ ((visibility("default")))
    #define PONG_MSGS_LOCAL  __attribute__ ((visibility("hidden")))
  #else
    #define PONG_MSGS_PUBLIC
    #define PONG_MSGS_LOCAL
  #endif
  #define PONG_MSGS_PUBLIC_TYPE
#endif
#endif  // PONG_MSGS__VISIBILITY_CONTROL_H_
// Generated 15-Jun-2026 14:31:16
 