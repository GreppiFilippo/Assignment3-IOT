#ifndef __CONNECTION_SERVICE__
#define __CONNECTION_SERVICE__

class ConnectionService
{
   private:
    bool connected = false;

   public:
    virtual void init() = 0;
    virtual void connect() = 0;
    bool isConnected() { return connected; }
};

#endif  // __CONNECTION_SERVICE__
