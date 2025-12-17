# Ngrok setup
  - Using tunnelling tools
    - if both client and service are connected to the same LAN, with no firewalls or port blocked, no problem
    - if instead the server/service has not a public IP (e.g. being connected to a hotspot – smartphone + Tethering), then we need to use a [tool for tunnelling](https://alternativeto.net/software/ngrok/). 
    - A main example is [ngrok](http://ngrok.com). By spawning the tool, one gets a public IP, to be used in client programs.  One can specify which web protocol to assume (http or https) - default is https, to force http the option `–scheme http` must be used 
    - Example: setting up a public IP address reachable through http, forwarding to a local http server on port 8080: 

        `ngrok http 8080 --scheme http,https`
        
        where `8080` is the local port where we want to forward the stream

    - An example of dynamically assigned IP: http://c037-137-204-20-125.ngrok-free.app 
