#ifndef __CONTEXT__
#define __CONTEXT__

class Context
{
   private:
    float waterLevel;

   public:
    Context();
    void setWaterLevel(float level);
    void populateJsonDocument(JsonDocument& doc);
};

#endif  // __CONTEXT__
