"""Fetch a bounded source list and build a reviewed, source-linked local corpus.

Retains short excerpts and original paraphrased notes, not full copyrighted pages.
Run manually to check sources again. Changed pages require review before notes update.
"""
import hashlib,json,re,urllib.request
from html.parser import HTMLParser
from pathlib import Path
from datetime import datetime,timezone
from concurrent.futures import ThreadPoolExecutor

ROOT=Path(__file__).resolve().parent/'knowledge_base'
# Notes below were reviewed against the linked public documentation on 2026-09-08.
SOURCES=[
 ('dell_forms','Dell: Server technology','https://www.dell.com/en-us/lp/server-technology','Tower servers',[
 ('rack_servers','Rack mounting','Rack servers fit into equipment racks, allowing multiple devices to be stacked vertically. This conserves floor space and organizes connections.'),
 ('rack_servers','Rack units','Server height is expressed in rack units. One unit, 1U, is approximately 1.75 inches; a 2U server occupies two units.'),
 ('tower_servers','Standalone enclosure','A tower server has a standalone enclosure resembling a desktop tower. It can suit offices that need a few servers without dedicated rack infrastructure.'),
 ('tower_servers','Office use case','Dell identifies small and remote offices as environments for tower servers. Common server services include shared files, messaging and web applications.'),
 ('server_purpose','Business applications','Documented server applications include file sharing, printing, email, web serving, backup, virtualization and analytics.'),
 ('blade_servers','Enclosure infrastructure','Blade modules sit side by side within a chassis that provides shared power, cabling and cooling.')]),
 ('lenovo_nic','Lenovo: Network interface cards','https://www.lenovo.com/us/en/glossary/nic/','network interface',[
 ('network','NIC purpose','A network interface card connects a computer to a network. It handles sending and receiving data through the supported connection.'),
 ('network','Wired and wireless interfaces','Network adapters can support wired Ethernet or wireless networking. Choose an interface compatible with the system and the network it must connect to.'),
 ('network','Network access example','A network interface enables access to services such as shared files and Internet applications. The adapter supplies connectivity, while application software provides the service.')]),
 ('ibm_blade','IBM: Blade servers','https://www.ibm.com/think/topics/blade-server','blade',[
 ('server_purpose','Client/server purpose','Servers supply services to client programs and people. The client/server arrangement separates requesting a service from providing it.'),
 ('server_architecture','Modular architecture','A blade system combines compute modules, an enclosure and a backplane. The backplane connects blades to shared infrastructure.'),
 ('blade_servers','Blade components','A blade contains processors, memory and adapters. Several blades fit inside an enclosure rather than operating as independent desktop cases.'),
 ('blade_servers','Shared resources','Blade enclosures can share power and cooling resources. Modular compute capacity can be expanded by adding supported blades.'),
 ('rack_servers','Rack versus blade','Rack-mounted servers can operate as separately managed systems. Blade designs depend more on an enclosing modular infrastructure.'),
 ('tower_servers','Tower services','A tower server can provide dedicated services such as DNS name resolution or DHCP address assignment. Server form and service role are separate ideas.')]),
 ('cloudflare_internet','Cloudflare: How the Internet works','https://www.cloudflare.com/learning/network-layer/how-does-the-internet-work/','HTTP',[
 ('server_purpose','Web request example','When a browser requests a page, the server returns web content. HTML, CSS and JavaScript can travel back as network packets.'),
 ('server_architecture','Requests and protocols','HTTP describes web requests and responses. IP addresses identify destinations; packets cross interconnected networks to reach them.'),
 ('network','Network data transfer','Network communication moves data in packets. Routers forward packets between networks; protocols let different systems exchange understandable messages.'),
 ('server_purpose','DNS before a request','DNS translates a domain name into an IP address. This helps the browser locate the server before requesting the website.')]),
 ('ibm_cpu','IBM: Central processing unit','https://www.ibm.com/think/topics/central-processing-unit','arithmetic',[
 ('cpu','Instruction processing','A CPU executes program instructions. A simplified instruction cycle consists of fetching an instruction, decoding it and executing it.'),
 ('cpu','Arithmetic and logic','The arithmetic/logic unit performs calculations and comparisons. These operations let software compute totals and make decisions based on data.'),
 ('cpu','Control and clock','Control circuitry coordinates instruction processing. A clock supplies timing signals used to synchronize processor operations.'),
 ('cpu','Cache and registers','CPU registers hold immediately needed values. Cache provides fast access to frequently used instructions and data, reducing reliance on slower memory accesses.'),
 ('server_architecture','Connecting computation','Computer buses carry data between components. CPU work relies on data movement as well as instruction execution.')]),
 ('kingston_memory','Kingston: Server memory support','https://www.kingston.com/en/support/technical/products/server-memory','ECC',[
 ('ram','ECC memory','Error-correcting code memory detects and corrects supported memory errors. Server platforms require compatible memory-controller and module support.'),
 ('ram','Memory speed limits','Memory speed depends on the CPU, platform and modules installed per channel. A faster-rated DIMM may run slower when the processor or population rules impose a limit.'),
 ('ram','Upgrade example','A DDR5 module rated at 6400 MT/s can operate at 5600 MT/s when that is the processor limit. The module rating does not override platform limits.'),
 ('ram','Module compatibility','Registered and unbuffered memory have different electrical designs. Follow the server manufacturer’s supported module types and population rules instead of mixing arbitrary DIMMs.'),
 ('motherboard','Platform compatibility','The motherboard and chipset influence which memory configurations are supported. Consult the system manual before selecting modules or filling slots.')]),
 ('ibm_storage','IBM: Data storage','https://www.ibm.com/think/topics/data-storage','RAM',[
 ('ram','Working memory versus storage','RAM supplies short-term working memory for active computation. Persistent storage keeps data for later use; memory and storage serve different purposes.'),
 ('storage_interface','Storage devices and systems','Storage retains digital information. HDDs, SSDs and networked storage are different ways of providing capacity and access to that information.'),
 ('server_architecture','Storage organization','Storage may be directly attached or delivered through networked systems. Architecture determines how applications reach their stored data.')]),
 ('supermicro_board','Supermicro: X14SBGM motherboard features','https://www.supermicro.com/en/support/manuals/product/motherboard/x14sbgm/Content/introduction/quick-reference/motherboard-features-x14sbgm.htm','Processor',[
 ('motherboard','A real server board','The X14SBGM documents a processor socket, DIMM slots, PCIe connections, BIOS and monitoring features. A motherboard defines a specific set of supported connections and components.'),
 ('motherboard','Not all functions are integrated','This board lists no onboard network controller and uses an external BMC module. Do not assume every server motherboard integrates networking, graphics or management in the same way.'),
 ('ram','Board-specific memory example','This board documents 16 DIMM slots for supported RDIMM configurations. Supported memory speed depends on the processor and the number of DIMMs per channel.'),
 ('bmc','Management varies by platform','An external BMC module is specified for this board. Management hardware is platform-specific rather than always a chip in one universal location.'),
 ('motherboard','Hardware monitoring','Documented monitoring includes voltages and temperatures for components such as the CPU and DIMMs. Fan and thermal support help the system supervise hardware conditions.')]),
 ('ibm_nvme','IBM: NVMe','https://www.ibm.com/think/topics/nvme','NVMe',[
 ('storage_interface','NVMe definition','NVMe is a storage protocol designed for nonvolatile media with parallel command handling and reduced I/O overhead.'),
 ('storage_interface','SSD versus NVMe','An SSD is a storage device; NVMe is a protocol used to communicate with compatible storage. Some SSDs instead use SATA or SAS interfaces.'),
 ('storage_interface','PCIe and fabrics','Local NVMe storage commonly communicates over PCIe. NVMe over Fabrics extends the protocol across supported interconnects such as Ethernet or Fibre Channel.'),
 ('storage_interface','Database use case','Low-latency storage access and parallel I/O can benefit busy database and analytics workloads. Actual gains depend on the workload and complete system.'),
 ('storage_interface','SATA and SAS','SATA and SAS are established storage interfaces also used by HDDs and some SSDs. Interface support matters when selecting replacement drives.')]),
 ('dell_power','Dell: Server power supplies','https://www.dell.com/en-us/shopping/server-power-supplies','convert',[
 ('psu','Power conversion','An AC server power supply converts incoming AC electricity into stable DC power used by server components.'),
 ('psu','Reliable operation','Power supply selection must suit the server’s electrical demand and supported configuration. A dependable power subsystem supports continuous operation.'),
 ('psu','Replacement compatibility','Choose a power supply supported by the particular server. Capacity and electrical compatibility matter as well as the physical shape.')]),
 ('dell_bmc','Dell: PowerEdge C system management guide','https://poweredgec.dell.com/files/QSG_PowerEdge_C_System_Management.pdf','BMC',[
 ('bmc','BMC purpose','Dell PowerEdge C management documentation describes BMC-based hardware monitoring and administration, including remote power-on capabilities.'),
 ('bmc','Management documentation','Management tools and supported features differ by PowerEdge C platform. Use the matching platform guide rather than assuming every controller offers identical functions.')]),
 ('dell_bmc_security','Dell: BMC and BIOS recommendations','https://infohub.delltechnologies.com/en-us/l/dell-powerprotect-dd-series-appliances-security/baseboard-management-controller-and-bios-recommendations/','isolated',[
 ('bmc','Management network isolation','Dell recommends keeping management access on an isolated network and not exposing that network directly to the Internet.'),
 ('bmc','Credentials and firmware','Dell recommends strong management credentials and current BMC and BIOS firmware. Follow the platform’s maintenance procedures when applying updates.')]),
 ('ibm_gpu','IBM: Graphics processing unit','https://www.ibm.com/think/topics/gpu','parallel',[
 ('gpu','Parallel computation','GPUs accelerate suitable work by carrying out many operations in parallel. They are used for graphics and for computational workloads beyond graphics.'),
 ('gpu','Rendering and simulation examples','GPU uses include 3D rendering, visualization and scientific simulation. These workloads can contain many similar calculations that benefit from parallel execution.'),
 ('gpu','AI example','GPU computation supports machine-learning training and inference. IBM identifies its Vela AI supercomputer as an example of GPU-powered infrastructure.'),
 ('gpu','Accelerator differences','Other accelerators include NPUs aimed at neural-network workloads and programmable FPGAs. Processor choice depends on the required computation.'),
 ('gpu','CPU comparison','CPUs handle general program execution while GPUs specialize in suitable parallel computation. Workload and software support determine whether an accelerator helps.')]),
]

class TextParser(HTMLParser):
    def __init__(self):super().__init__();self.skip=0;self.parts=[];self.title=[];self.in_title=False
    def handle_starttag(self,tag,attrs):
        if tag in ('script','style','noscript'):self.skip+=1
        if tag=='title':self.in_title=True
    def handle_endtag(self,tag):
        if tag in ('script','style','noscript'):self.skip=max(0,self.skip-1)
        if tag=='title':self.in_title=False
    def handle_data(self,data):
        if not self.skip:
            self.parts.append(data)
            if self.in_title:self.title.append(data)

def fetch(source):
    sid,title,url,keyword,notes=source
    result=dict(id=sid,title=title,url=url,reviewed_at='2026-09-08',collected_at=datetime.now(timezone.utc).isoformat())
    try:
        request=urllib.request.Request(url,headers={'User-Agent':'ServerLessonCollector/1.0 (educational local knowledge base)'})
        with urllib.request.urlopen(request,timeout=25) as response:
            raw=response.read(6_000_000);result['final_url']=response.url
        if raw.startswith(b'%PDF'):
            result.update(fetch_status='downloaded_pdf_web_reviewed',sha256=hashlib.sha256(raw).hexdigest(),excerpt='')
            return result
        parser=TextParser();parser.feed(raw.decode('utf-8',errors='replace'))
        body=re.sub(r'\s+',' ',' '.join(parser.parts)).strip()
        if len(body)<500 or 'Access Denied' in ''.join(parser.title):raise ValueError('Source did not return a readable article')
        pos=body.lower().find(keyword.lower());result.update(fetch_status='downloaded',sha256=hashlib.sha256(raw).hexdigest(),extracted_characters=len(body),excerpt=' '.join(body[max(pos,0):].split()[:20]))
    except Exception as error:
        result.update(fetch_status='web_verified_fetch_unavailable',fetch_error=type(error).__name__,excerpt='')
    return result

def main():
    ROOT.mkdir(exist_ok=True)
    with ThreadPoolExecutor(max_workers=4) as pool:sources=list(pool.map(fetch,SOURCES))
    chunks=[]
    for sid,title,url,keyword,notes in SOURCES:
        for number,(topic,heading,text) in enumerate(notes,1):
            chunks.append(dict(id=f'{sid}_{number}',topic_id=topic,heading=heading,text=text,source_id=sid,source_title=title,url=url,kind='reviewed_paraphrase',reviewed_at='2026-09-08'))
    payload=dict(schema_version=1,built_at=datetime.now(timezone.utc).isoformat(),sources=sources,chunks=chunks)
    (ROOT/'knowledge.json').write_text(json.dumps(payload,indent=2,ensure_ascii=False),encoding='utf-8')
    report=['# Server Infrastructure · Collected knowledge','', 'Source-linked, reviewed paraphrases and brief scraped excerpts. Collection checks do not automatically rewrite reviewed notes.','']
    for topic in dict.fromkeys(c['topic_id'] for c in chunks):
        report.extend(['## '+topic.replace('_',' ').title(),''])
        for c in chunks:
            if c['topic_id']==topic:report.extend(['### '+c['heading'],c['text'],f"Source: [{c['source_title']}]({c['url']})",''])
    (ROOT/'Collected_Knowledge.md').write_text('\n'.join(report),encoding='utf-8')
    print(json.dumps(dict(sources=len(sources),chunks=len(chunks),topics=len(set(c['topic_id'] for c in chunks)),downloads=[(s['id'],s['fetch_status']) for s in sources])))
if __name__=='__main__':main()
