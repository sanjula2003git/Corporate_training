"""Illustrative real-world scenarios, not claims about named deployments."""
EXAMPLES = {
 'server_purpose': [
 ('Sharing office files', 'An employee opens a shared project folder.', 'A file server checks their access and sends the requested document over the network.', 'Colleagues can work with centrally managed files rather than emailing separate copies.'),
 ('Playing an online match', 'Several players join the same multiplayer game.', 'A game server receives their actions, updates the shared match state and sends results back.', 'Players see a coordinated match; the server provides the shared service.'),
 ('Signing in at college', 'A student signs in to a learning portal.', 'An authentication service checks the submitted credentials and returns the sign-in result.', 'The portal can control who accesses lessons and submissions.')],
 'server_architecture': [
 ('Searching a shop catalogue', 'A customer searches for a product.', 'The network interface receives the request; the CPU runs search logic using RAM and, when needed, database data from storage.', 'The response travels back over the network. Several components cooperate on one request.'),
 ('Hosting virtual classrooms', 'A school runs several virtual machines on one physical server.', 'A hypervisor allocates CPU time and RAM, while storage keeps each virtual machine’s files and the network carries student requests.', 'Architecture determines how these resources are shared between services.'),
 ('Serving a popular video', 'Many viewers request the same video segment.', 'Server software may reuse a segment already in RAM, while the network interface transfers it to viewers.', 'A cached request can avoid another drive read; not every request follows exactly the same path.')],
 'rack_servers': [
 ('An office server room', 'A company needs several separate servers in a small room.', 'Technicians mount rack servers on rails in a cabinet and organize network cables and power connections.', 'The standard mounting format makes equipment easier to arrange and service.'),
 ('Adding website capacity', 'A hosting team needs another physical web server.', 'They install a rack server in available rack space, connect power and networking, and configure its software.', 'Capacity grows by adding equipment; the rack itself does not run the website.'),
 ('Replacing a failed drive', 'A rack server reports a failed hot-swappable drive.', 'With a supported redundant storage configuration, a technician can replace the accessible drive while following the system’s service procedure.', 'Rack layout helps service access, but hot-swap and redundancy depend on the actual hardware.')],
 'blade_servers': [
 ('A dense compute cluster', 'A team needs many compute nodes in one enclosure.', 'Each blade supplies compute resources while the enclosure provides shared infrastructure such as power, cooling and networking.', 'Many server nodes can fit together, but they depend on the enclosure.'),
 ('Adding a compatible node', 'An organization has an empty bay in its blade enclosure.', 'A technician installs a compatible blade and provisions it through the enclosure’s management tools.', 'A blade is designed for its enclosure; it is not simply a tower placed on its side.'),
 ('Planning shared capacity', 'A team wants to fill the remaining blade bays.', 'They check enclosure power, cooling and network capacity before adding nodes.', 'Shared infrastructure must support the combined workload, not just each individual blade.')],
 'tower_servers': [
 ('A small design office', 'Five designers need shared project storage but have no rack cabinet.', 'A tower server sits in a suitable ventilated location and runs a file service.', 'The tower form can suit a small installation without rack mounting.'),
 ('A local workshop', 'A workshop wants an on-site inventory application.', 'A tower server runs the application and database while staff computers connect over the local network.', 'Its case shape differs from a rack server, but it can provide the same kinds of services.'),
 ('A training laboratory', 'Students need a standalone machine for learning server administration.', 'An instructor uses a tower server to run practice virtual machines.', 'Tower describes the physical form; the operating system and applications determine its role.')],
 'cpu': [
 ('Calculating a shopping basket', 'You buy two notebooks from an online shop. Each notebook costs ₹50.', 'The shop’s server CPU runs the program that calculates 2 × ₹50 = ₹100. If delivery costs ₹20, it adds that to get ₹120.', 'The shop sends your browser the ₹120 total. The CPU did the calculation; the network carried the answer back to you.'),
 ('Processing a game move', 'A player makes a move in an online game.', 'The server CPU runs game rules to check the move and update the match state.', 'The CPU executes the rules; the network interface transports the messages.'),
 ('Generating a monthly report', 'A manager requests a sales report.', 'The CPU executes filtering, grouping and arithmetic instructions on the retrieved records.', 'A CPU-bound report may take longer when other jobs compete for processor time.')],
 'ram': [
 ('Keeping a product catalogue ready', 'A shop repeatedly receives requests for popular products.', 'Its server keeps frequently used catalogue data in RAM so software can access that working data quickly.', 'This cache can reduce drive reads; the durable catalogue still belongs in persistent storage.'),
 ('Running several virtual machines', 'A training server runs six student virtual machines.', 'Each active machine needs RAM for its operating system and running programs.', 'If memory is insufficient, paging or allocation failures can slow or prevent work; more RAM helps capacity, not every calculation.'),
 ('Editing a video on a render server', 'A render job processes a sequence of frames.', 'RAM holds active frame data and program state while the CPU or GPU processes it.', 'Working data needs memory; finished output must be saved to storage to survive power loss.')],
 'motherboard': [
 ('Assembling a server', 'A technician installs processors and memory.', 'They place a compatible CPU into its motherboard socket and supported RAM into its slots.', 'The motherboard provides the physical and electrical connections; parts must match its specifications.'),
 ('Adding a network card', 'A server needs an additional network connection.', 'A supported network adapter is fitted to a compatible motherboard expansion slot.', 'The board links the adapter to the rest of the system through the relevant bus.'),
 ('Planning a memory upgrade', 'An administrator wants to double installed RAM.', 'They check motherboard slot count, processor memory support and permitted module configurations.', 'Physical space alone is not enough; the complete platform must support the upgrade.')],
 'network': [
 ('Downloading a backup', 'A workstation retrieves a large backup from a server.', 'The server’s network interface sends the backup data as network traffic over its connection.', 'The interface’s capacity can limit transfer speed, alongside the network path and storage.'),
 ('Opening a class portal', 'Thirty students open a lesson at once.', 'The network interface receives incoming requests and transmits the server’s responses.', 'It provides connectivity; it does not itself run the lesson application.'),
 ('Connecting separate networks', 'A server needs connections to two different network segments.', 'Administrators configure suitable network interfaces and routing or isolation rules.', 'Extra ports provide connection options, but the configuration determines how traffic flows.')],
 'storage_interface': [
 ('Reading a database record', 'A requested database page is not already in RAM.', 'The server communicates with the storage device through its supported interface, such as NVMe over PCIe, to retrieve data.', 'The interface carries storage commands and data; the device retains the records.'),
 ('Upgrading a server drive', 'A technician wants to replace a SATA drive with an NVMe drive.', 'They check connectors, backplane and platform support before choosing the replacement.', 'Different storage interfaces are not automatically interchangeable, even if devices look similar.'),
 ('Writing a nightly backup', 'Backup software saves data to attached storage.', 'Commands and data pass through the relevant controller and storage interface to the drives.', 'A slow interface can constrain throughput, but drive performance and the workload also matter.')],
 'psu': [
 ('Powering a server', 'An administrator plugs a server into an appropriate electrical supply.', 'Its power supply converts incoming electrical power into the regulated DC outputs the server needs.', 'The PSU supplies usable power; the CPU and other components perform the computing.'),
 ('A redundant supply fails', 'One PSU fails in a correctly configured server with sufficient redundant capacity.', 'The remaining supply can continue providing power while the failed unit is serviced according to its procedure.', 'Redundancy can tolerate one supply failure, but only when capacity and configuration support it.'),
 ('Adding a GPU', 'A team plans to install a power-hungry accelerator.', 'They check the server’s power budget, supported connectors and PSU configuration.', 'An expansion slot does not guarantee enough electrical power for the new component.')],
 'bmc': [
 ('A server stops responding', 'An administrator cannot reach the operating system remotely.', 'If the management controller remains powered and reachable, it may provide a remote console, hardware status or supported power controls.', 'Management access can help even when the main operating system is unavailable.'),
 ('Investigating overheating', 'A server reports a temperature warning.', 'The management controller exposes sensor readings and hardware events for the administrator to inspect.', 'It helps diagnose cooling problems; it does not replace the fans or heatsinks.'),
 ('Checking a distant machine', 'A server is located in another building.', 'An authorized administrator uses the management controller’s interface to review supported hardware health information.', 'Remote hardware management reduces some on-site visits and requires properly protected access.')],
 'gpu': [
 ('Rendering an animated scene', 'A studio submits a scene to a GPU-compatible renderer.', 'The GPU executes many suitable rendering operations in parallel while software and the CPU coordinate the job.', 'Parallel work can finish faster; the application must support GPU acceleration.'),
 ('Training an image classifier', 'A research team trains a model on image examples.', 'A supported GPU performs large batches of matrix operations used by the training software.', 'Its parallel processing suits this workload, but data movement and available GPU memory still matter.'),
 ('Processing many video frames', 'A service needs to transform a large batch of video frames.', 'Compatible software sends supported processing tasks to an accelerator.', 'Acceleration depends on the hardware and software; installing a GPU does not speed up every server task.')],
}

def next_example(topic_id, history, avoid=''):
    """Return an unused scenario; report exhaustion instead of silently looping."""
    previous='\n'.join(m.get('content','') for m in history if m.get('role')=='assistant')
    avoided=[v.strip().lower() for v in avoid.split(',') if v.strip()]
    for title,trigger,work,outcome in EXAMPLES[topic_id]:
        if title in previous:continue
        if any(v in ' '.join((title,trigger,work,outcome)).lower() for v in avoided):continue
        return f'**Real-world example: {title}**\n\n**Situation:** {trigger}\n\n**What this part does:** {work}\n\n**Why it matters:** {outcome}'
    return None
