#include "Context.hpp"

Context::Context(){
    this->waterLevel = 0.0f;
}

void Context::setWaterLevel(float level){
    this->waterLevel = level;
}