#ifndef __CONNECTION_SERVICE__
#define __CONNECTION_SERVICE__

class ConnectionService
{
   protected:
    bool connected = false;

   public:
    virtual void init() = 0;
    virtual void connect() = 0;
    virtual void send(const char* data, size_t length) = 0;
    bool isConnected() { return connected; }
};

#endif  // __CONNECTION_SERVICE__
