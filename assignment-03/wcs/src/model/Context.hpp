#ifndef __CONTEXT__
#define __CONTEXT__

class Context 
{
    public:
        enum Mode {
            UNCONNECTED,
            AUTOMATIC,
            MANUAL
        };
        Context();
        int getValveOpening();
        Mode getMode();
    private:
        Mode mode;
        int valveOpening;
        void setValveOpening(int opening);
        void setMode(Mode mode);
}; 

#endif