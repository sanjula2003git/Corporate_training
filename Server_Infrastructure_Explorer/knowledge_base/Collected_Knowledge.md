# Server Infrastructure · Collected knowledge

Source-linked, reviewed paraphrases and brief scraped excerpts. Collection checks do not automatically rewrite reviewed notes.

## Rack Servers

### Rack mounting
Rack servers fit into equipment racks, allowing multiple devices to be stacked vertically. This conserves floor space and organizes connections.
Source: [Dell: Server technology](https://www.dell.com/en-us/lp/server-technology)

### Rack units
Server height is expressed in rack units. One unit, 1U, is approximately 1.75 inches; a 2U server occupies two units.
Source: [Dell: Server technology](https://www.dell.com/en-us/lp/server-technology)

### Rack versus blade
Rack-mounted servers can operate as separately managed systems. Blade designs depend more on an enclosing modular infrastructure.
Source: [IBM: Blade servers](https://www.ibm.com/think/topics/blade-server)

## Tower Servers

### Standalone enclosure
A tower server has a standalone enclosure resembling a desktop tower. It can suit offices that need a few servers without dedicated rack infrastructure.
Source: [Dell: Server technology](https://www.dell.com/en-us/lp/server-technology)

### Office use case
Dell identifies small and remote offices as environments for tower servers. Common server services include shared files, messaging and web applications.
Source: [Dell: Server technology](https://www.dell.com/en-us/lp/server-technology)

### Tower services
A tower server can provide dedicated services such as DNS name resolution or DHCP address assignment. Server form and service role are separate ideas.
Source: [IBM: Blade servers](https://www.ibm.com/think/topics/blade-server)

## Server Purpose

### Business applications
Documented server applications include file sharing, printing, email, web serving, backup, virtualization and analytics.
Source: [Dell: Server technology](https://www.dell.com/en-us/lp/server-technology)

### Client/server purpose
Servers supply services to client programs and people. The client/server arrangement separates requesting a service from providing it.
Source: [IBM: Blade servers](https://www.ibm.com/think/topics/blade-server)

### Web request example
When a browser requests a page, the server returns web content. HTML, CSS and JavaScript can travel back as network packets.
Source: [Cloudflare: How the Internet works](https://www.cloudflare.com/learning/network-layer/how-does-the-internet-work/)

### DNS before a request
DNS translates a domain name into an IP address. This helps the browser locate the server before requesting the website.
Source: [Cloudflare: How the Internet works](https://www.cloudflare.com/learning/network-layer/how-does-the-internet-work/)

## Blade Servers

### Enclosure infrastructure
Blade modules sit side by side within a chassis that provides shared power, cabling and cooling.
Source: [Dell: Server technology](https://www.dell.com/en-us/lp/server-technology)

### Blade components
A blade contains processors, memory and adapters. Several blades fit inside an enclosure rather than operating as independent desktop cases.
Source: [IBM: Blade servers](https://www.ibm.com/think/topics/blade-server)

### Shared resources
Blade enclosures can share power and cooling resources. Modular compute capacity can be expanded by adding supported blades.
Source: [IBM: Blade servers](https://www.ibm.com/think/topics/blade-server)

## Network

### NIC purpose
A network interface card connects a computer to a network. It handles sending and receiving data through the supported connection.
Source: [Lenovo: Network interface cards](https://www.lenovo.com/us/en/glossary/nic/)

### Wired and wireless interfaces
Network adapters can support wired Ethernet or wireless networking. Choose an interface compatible with the system and the network it must connect to.
Source: [Lenovo: Network interface cards](https://www.lenovo.com/us/en/glossary/nic/)

### Network access example
A network interface enables access to services such as shared files and Internet applications. The adapter supplies connectivity, while application software provides the service.
Source: [Lenovo: Network interface cards](https://www.lenovo.com/us/en/glossary/nic/)

### Network data transfer
Network communication moves data in packets. Routers forward packets between networks; protocols let different systems exchange understandable messages.
Source: [Cloudflare: How the Internet works](https://www.cloudflare.com/learning/network-layer/how-does-the-internet-work/)

## Server Architecture

### Modular architecture
A blade system combines compute modules, an enclosure and a backplane. The backplane connects blades to shared infrastructure.
Source: [IBM: Blade servers](https://www.ibm.com/think/topics/blade-server)

### Requests and protocols
HTTP describes web requests and responses. IP addresses identify destinations; packets cross interconnected networks to reach them.
Source: [Cloudflare: How the Internet works](https://www.cloudflare.com/learning/network-layer/how-does-the-internet-work/)

### Connecting computation
Computer buses carry data between components. CPU work relies on data movement as well as instruction execution.
Source: [IBM: Central processing unit](https://www.ibm.com/think/topics/central-processing-unit)

### Storage organization
Storage may be directly attached or delivered through networked systems. Architecture determines how applications reach their stored data.
Source: [IBM: Data storage](https://www.ibm.com/think/topics/data-storage)

## Cpu

### Instruction processing
A CPU executes program instructions. A simplified instruction cycle consists of fetching an instruction, decoding it and executing it.
Source: [IBM: Central processing unit](https://www.ibm.com/think/topics/central-processing-unit)

### Arithmetic and logic
The arithmetic/logic unit performs calculations and comparisons. These operations let software compute totals and make decisions based on data.
Source: [IBM: Central processing unit](https://www.ibm.com/think/topics/central-processing-unit)

### Control and clock
Control circuitry coordinates instruction processing. A clock supplies timing signals used to synchronize processor operations.
Source: [IBM: Central processing unit](https://www.ibm.com/think/topics/central-processing-unit)

### Cache and registers
CPU registers hold immediately needed values. Cache provides fast access to frequently used instructions and data, reducing reliance on slower memory accesses.
Source: [IBM: Central processing unit](https://www.ibm.com/think/topics/central-processing-unit)

## Ram

### ECC memory
Error-correcting code memory detects and corrects supported memory errors. Server platforms require compatible memory-controller and module support.
Source: [Kingston: Server memory support](https://www.kingston.com/en/support/technical/products/server-memory)

### Memory speed limits
Memory speed depends on the CPU, platform and modules installed per channel. A faster-rated DIMM may run slower when the processor or population rules impose a limit.
Source: [Kingston: Server memory support](https://www.kingston.com/en/support/technical/products/server-memory)

### Upgrade example
A DDR5 module rated at 6400 MT/s can operate at 5600 MT/s when that is the processor limit. The module rating does not override platform limits.
Source: [Kingston: Server memory support](https://www.kingston.com/en/support/technical/products/server-memory)

### Module compatibility
Registered and unbuffered memory have different electrical designs. Follow the server manufacturer’s supported module types and population rules instead of mixing arbitrary DIMMs.
Source: [Kingston: Server memory support](https://www.kingston.com/en/support/technical/products/server-memory)

### Working memory versus storage
RAM supplies short-term working memory for active computation. Persistent storage keeps data for later use; memory and storage serve different purposes.
Source: [IBM: Data storage](https://www.ibm.com/think/topics/data-storage)

### Board-specific memory example
This board documents 16 DIMM slots for supported RDIMM configurations. Supported memory speed depends on the processor and the number of DIMMs per channel.
Source: [Supermicro: X14SBGM motherboard features](https://www.supermicro.com/en/support/manuals/product/motherboard/x14sbgm/Content/introduction/quick-reference/motherboard-features-x14sbgm.htm)

## Motherboard

### Platform compatibility
The motherboard and chipset influence which memory configurations are supported. Consult the system manual before selecting modules or filling slots.
Source: [Kingston: Server memory support](https://www.kingston.com/en/support/technical/products/server-memory)

### A real server board
The X14SBGM documents a processor socket, DIMM slots, PCIe connections, BIOS and monitoring features. A motherboard defines a specific set of supported connections and components.
Source: [Supermicro: X14SBGM motherboard features](https://www.supermicro.com/en/support/manuals/product/motherboard/x14sbgm/Content/introduction/quick-reference/motherboard-features-x14sbgm.htm)

### Not all functions are integrated
This board lists no onboard network controller and uses an external BMC module. Do not assume every server motherboard integrates networking, graphics or management in the same way.
Source: [Supermicro: X14SBGM motherboard features](https://www.supermicro.com/en/support/manuals/product/motherboard/x14sbgm/Content/introduction/quick-reference/motherboard-features-x14sbgm.htm)

### Hardware monitoring
Documented monitoring includes voltages and temperatures for components such as the CPU and DIMMs. Fan and thermal support help the system supervise hardware conditions.
Source: [Supermicro: X14SBGM motherboard features](https://www.supermicro.com/en/support/manuals/product/motherboard/x14sbgm/Content/introduction/quick-reference/motherboard-features-x14sbgm.htm)

## Storage Interface

### Storage devices and systems
Storage retains digital information. HDDs, SSDs and networked storage are different ways of providing capacity and access to that information.
Source: [IBM: Data storage](https://www.ibm.com/think/topics/data-storage)

### NVMe definition
NVMe is a storage protocol designed for nonvolatile media with parallel command handling and reduced I/O overhead.
Source: [IBM: NVMe](https://www.ibm.com/think/topics/nvme)

### SSD versus NVMe
An SSD is a storage device; NVMe is a protocol used to communicate with compatible storage. Some SSDs instead use SATA or SAS interfaces.
Source: [IBM: NVMe](https://www.ibm.com/think/topics/nvme)

### PCIe and fabrics
Local NVMe storage commonly communicates over PCIe. NVMe over Fabrics extends the protocol across supported interconnects such as Ethernet or Fibre Channel.
Source: [IBM: NVMe](https://www.ibm.com/think/topics/nvme)

### Database use case
Low-latency storage access and parallel I/O can benefit busy database and analytics workloads. Actual gains depend on the workload and complete system.
Source: [IBM: NVMe](https://www.ibm.com/think/topics/nvme)

### SATA and SAS
SATA and SAS are established storage interfaces also used by HDDs and some SSDs. Interface support matters when selecting replacement drives.
Source: [IBM: NVMe](https://www.ibm.com/think/topics/nvme)

## Bmc

### Management varies by platform
An external BMC module is specified for this board. Management hardware is platform-specific rather than always a chip in one universal location.
Source: [Supermicro: X14SBGM motherboard features](https://www.supermicro.com/en/support/manuals/product/motherboard/x14sbgm/Content/introduction/quick-reference/motherboard-features-x14sbgm.htm)

### BMC purpose
Dell PowerEdge C management documentation describes BMC-based hardware monitoring and administration, including remote power-on capabilities.
Source: [Dell: PowerEdge C system management guide](https://poweredgec.dell.com/files/QSG_PowerEdge_C_System_Management.pdf)

### Management documentation
Management tools and supported features differ by PowerEdge C platform. Use the matching platform guide rather than assuming every controller offers identical functions.
Source: [Dell: PowerEdge C system management guide](https://poweredgec.dell.com/files/QSG_PowerEdge_C_System_Management.pdf)

### Management network isolation
Dell recommends keeping management access on an isolated network and not exposing that network directly to the Internet.
Source: [Dell: BMC and BIOS recommendations](https://infohub.delltechnologies.com/en-us/l/dell-powerprotect-dd-series-appliances-security/baseboard-management-controller-and-bios-recommendations/)

### Credentials and firmware
Dell recommends strong management credentials and current BMC and BIOS firmware. Follow the platform’s maintenance procedures when applying updates.
Source: [Dell: BMC and BIOS recommendations](https://infohub.delltechnologies.com/en-us/l/dell-powerprotect-dd-series-appliances-security/baseboard-management-controller-and-bios-recommendations/)

## Psu

### Power conversion
An AC server power supply converts incoming AC electricity into stable DC power used by server components.
Source: [Dell: Server power supplies](https://www.dell.com/en-us/shopping/server-power-supplies)

### Reliable operation
Power supply selection must suit the server’s electrical demand and supported configuration. A dependable power subsystem supports continuous operation.
Source: [Dell: Server power supplies](https://www.dell.com/en-us/shopping/server-power-supplies)

### Replacement compatibility
Choose a power supply supported by the particular server. Capacity and electrical compatibility matter as well as the physical shape.
Source: [Dell: Server power supplies](https://www.dell.com/en-us/shopping/server-power-supplies)

## Gpu

### Parallel computation
GPUs accelerate suitable work by carrying out many operations in parallel. They are used for graphics and for computational workloads beyond graphics.
Source: [IBM: Graphics processing unit](https://www.ibm.com/think/topics/gpu)

### Rendering and simulation examples
GPU uses include 3D rendering, visualization and scientific simulation. These workloads can contain many similar calculations that benefit from parallel execution.
Source: [IBM: Graphics processing unit](https://www.ibm.com/think/topics/gpu)

### AI example
GPU computation supports machine-learning training and inference. IBM identifies its Vela AI supercomputer as an example of GPU-powered infrastructure.
Source: [IBM: Graphics processing unit](https://www.ibm.com/think/topics/gpu)

### Accelerator differences
Other accelerators include NPUs aimed at neural-network workloads and programmable FPGAs. Processor choice depends on the required computation.
Source: [IBM: Graphics processing unit](https://www.ibm.com/think/topics/gpu)

### CPU comparison
CPUs handle general program execution while GPUs specialize in suitable parallel computation. Workload and software support determine whether an accelerator helps.
Source: [IBM: Graphics processing unit](https://www.ibm.com/think/topics/gpu)
