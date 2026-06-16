"""Interview concept definitions for the Explain-It-Out-Loud practice panel."""

INTERVIEW_CONCEPTS = [
    # ── SystemVerilog / OOPS ──────────────────────────────────────────────────
    {
        "id": 1, "topic": "SystemVerilog", "skill": "OOPS", "difficulty": "E",
        "question": "What is the difference between 'logic' and 'reg' in SystemVerilog?",
        "answer": (
            "Both hold 4-state values (0, 1, X, Z). 'reg' is legacy Verilog — "
            "can only be driven inside procedural blocks (always/initial). 'logic' is SV's "
            "unified net/variable type: it can be driven by continuous assignments OR in "
            "procedural blocks. Key constraint: 'logic' cannot have multiple drivers (use "
            "'wire' for that). Best practice: use 'logic' everywhere in SV unless you "
            "specifically need multiple drivers."
        ),
    },
    {
        "id": 2, "topic": "SystemVerilog", "skill": "OOPS", "difficulty": "D",
        "question": "Explain interfaces and modports in SystemVerilog. Why are they critical in testbenches?",
        "answer": (
            "An interface bundles a group of signals into a named entity, reducing port-list "
            "clutter. You pass one interface handle instead of 20 individual signals.\n\n"
            "Modports (module ports) restrict visibility: 'master' modport may drive PADDR/PWDATA "
            "and read PRDATA; 'slave' modport is the reverse. This enforces directionality at "
            "compile time.\n\n"
            "Clocking blocks inside interfaces add synchronization: inputs are sampled 1 setup "
            "time BEFORE the clock edge, outputs are driven 1 hold time AFTER — eliminating "
            "race conditions in testbenches. Always use clocking blocks in verification, never "
            "raw @(posedge clk) assignments."
        ),
    },
    {
        "id": 3, "topic": "SystemVerilog", "skill": "OOPS", "difficulty": "D",
        "question": "Explain virtual functions, virtual classes, and polymorphism in SystemVerilog OOP.",
        "answer": (
            "virtual class: an abstract base class that cannot be instantiated directly — it "
            "defines the interface contract. Like an abstract base in C++.\n\n"
            "virtual function: a method that can be overridden in derived classes. When called "
            "through a base-class handle, the DERIVED class's version runs — this is runtime "
            "polymorphism.\n\n"
            "UVM uses this everywhere: uvm_component::run_phase() is virtual, so each component "
            "overrides it with its own behavior. The scheduler calls run_phase() through a base "
            "handle — each component does the right thing. Without 'virtual', the base class "
            "method always runs regardless of the actual object type."
        ),
    },
    # ── Constraints ───────────────────────────────────────────────────────────
    {
        "id": 4, "topic": "Constraints", "skill": "Constraints", "difficulty": "D",
        "question": "What is constraint solving in SystemVerilog? Explain 'rand', 'randc', 'solve...before', and 'dist'.",
        "answer": (
            "rand: variable randomized independently each call. randc: constraint-random cycling — "
            "generates all values in range before repeating (no duplicates until the set is exhausted).\n\n"
            "solve A before B: guides the solver to assign A first, then solve B based on A. "
            "Used when distributions depend on previously assigned values — e.g., solve len before data.\n\n"
            "dist: weighted distribution — {0:/10, 1:/90} means 10% chance of 0, 90% of 1. "
            "Colon-slash (:/) is weighted by ratio; colon-equal (:=) is weighted by absolute count.\n\n"
            "inside: set membership constraint. addr inside {[0:15], 32, 64}.\n\n"
            "Solver tries to satisfy ALL active constraints simultaneously. If unsatisfiable, "
            "randomize() returns 0 — always check the return value!"
        ),
    },
    {
        "id": 5, "topic": "Constraints", "skill": "Constraints", "difficulty": "C",
        "question": "Explain constraint inheritance, disable iff, and soft constraints.",
        "answer": (
            "Inheritance: child class constraints extend parent constraints — all are active "
            "unless explicitly disabled. Use constraint_mode(0) to disable a named constraint block.\n\n"
            "disable iff (expr): guard clause — the constraint is only enforced when the guard "
            "expression is false. Used for conditional constraints: 'if (mode == READ) { no write constraints }'.\n\n"
            "soft constraints (SV 2012): a preference, not a requirement. If satisfying a soft "
            "constraint conflicts with a hard constraint, the soft one is dropped silently. Useful "
            "for default values that test writers can override without disabling the whole block.\n\n"
            "Key debugging: if randomize() fails, use solve_order, remove constraints one by one, "
            "or print the constraint set to find the unsatisfiable clause."
        ),
    },
    # ── Assertions ────────────────────────────────────────────────────────────
    {
        "id": 6, "topic": "Assertions", "skill": "Assertions", "difficulty": "D",
        "question": "Explain SVA: immediate vs concurrent assertions, sequences, and properties.",
        "answer": (
            "Immediate assertion: evaluated at a point in time like an if-statement. "
            "assert (a == b); — fires the moment the simulator reaches this line. Used in "
            "procedural code.\n\n"
            "Concurrent assertion: evaluated over clock cycles. Declared with 'property' and "
            "sampled at the clock edge. Can span multiple cycles using ##N (cycle delays) and "
            "operators like |-> (overlapping implication) and |=> (non-overlapping).\n\n"
            "Sequence: a temporal pattern. seq1 = @(posedge clk) a ##1 b ##2 c — 'a' then 'b' "
            "one cycle later, then 'c' two cycles after.\n\n"
            "Property: a formal specification built from sequences. property p1; @(posedge clk) "
            "req |-> ##[1:4] ack; endproperty.\n\n"
            "assert property(p1): simulation check. cover property(p1): coverage. assume property(p1): "
            "constraint for formal verification."
        ),
    },
    {
        "id": 7, "topic": "Assertions", "skill": "Assertions", "difficulty": "C",
        "question": "Explain $past, $rose, $fell, $stable in SVA and give an example use case.",
        "answer": (
            "$past(sig, N): returns value of sig N cycles ago. Default is 1 cycle. "
            "Use: assert property(@(posedge clk) ack |-> $past(req,1)) — ack can only be high "
            "if req was high last cycle.\n\n"
            "$rose(sig): true when sig transitions 0→1 at the clock edge.\n"
            "$fell(sig): true when sig transitions 1→0.\n"
            "$stable(sig): true when sig didn't change since last clock.\n\n"
            "Example — check a handshake: "
            "req must stay stable until ack:\n"
            "property req_stable;\n"
            "  @(posedge clk) $rose(req) |-> req ##1 ($stable(req) until ack);\n"
            "endproperty\n\n"
            "These are sampled-value functions — they reference the sampled (pre-clock) value, "
            "not the current simulation delta."
        ),
    },
    # ── Covergroups ───────────────────────────────────────────────────────────
    {
        "id": 8, "topic": "Covergroups", "skill": "Covergroups", "difficulty": "D",
        "question": "What is functional coverage? Explain covergroups, coverpoints, and cross coverage.",
        "answer": (
            "Functional coverage measures HOW MUCH of the design spec has been exercised, "
            "not just which lines were executed (that's code coverage).\n\n"
            "Covergroup: a user-defined sampling container. Triggered at an event (clock edge, "
            "signal change, or manually via .sample()).\n\n"
            "Coverpoint: one dimension of coverage. coverpoint addr { bins low = {[0:15]}; "
            "bins high = {[240:255]}; bins other = default; }\n\n"
            "Automatic bins: by default, SV creates 64 bins for 4-state variables. "
            "Use binsof() to restrict. illegal_bins marks values that should never occur.\n\n"
            "Cross coverage: cartesian product of two coverpoints. "
            "cross addr, cmd — covers all (addr, cmd) pairs. Use binsof(addr.low) && binsof(cmd.write) "
            "to select specific cross bins.\n\n"
            "Goal: 100% functional coverage means all spec scenarios were exercised."
        ),
    },
    # ── UVM ───────────────────────────────────────────────────────────────────
    {
        "id": 9, "topic": "UVM", "skill": "UVM", "difficulty": "D",
        "question": "Describe the UVM phase mechanism. What happens in build_phase vs connect_phase vs run_phase?",
        "answer": (
            "UVM phases are ordered lifecycle stages that ALL components execute synchronously.\n\n"
            "build_phase (top-down): create child components and configure them. "
            "Parent builds before children. Use create() factory method, not 'new'. Set config objects.\n\n"
            "connect_phase (bottom-up): wire TLM ports between components. "
            "agent.monitor.ap.connect(scoreboard.analysis_export). Children connect before parents.\n\n"
            "run_phase (all components concurrently): time-consuming, uses fork/join. "
            "Sequences run here via start(). The phase ends when all run_phase tasks return "
            "(or drop_objection is called).\n\n"
            "start_of_simulation_phase: print topology. "
            "extract_phase: harvest results from scoreboards. "
            "check_phase: compare expected vs actual. "
            "report_phase: print summary.\n\n"
            "Key: raise_objection(this) before any consuming activity, drop_objection(this) when done."
        ),
    },
    {
        "id": 10, "topic": "UVM", "skill": "UVM", "difficulty": "C",
        "question": "Explain the UVM Factory pattern. Why do we use it and how does override work?",
        "answer": (
            "The UVM factory is a registry that maps type names to constructors. "
            "Instead of 'new', you call MyComp::type_id::create(name, parent).\n\n"
            "WHY: it enables type overrides without modifying testbench source. "
            "In your test, call: factory.set_type_override_by_type(MySeq::get_type(), MyExtSeq::get_type()). "
            "Every subsequent create() of MySeq now returns a MyExtSeq instead. Zero source edits needed.\n\n"
            "Instance override: override only components at a specific hierarchy path. "
            "set_inst_override_by_name(MySeq, MyExtSeq, 'env.agent.*').\n\n"
            "Registration: `uvm_component_utils(MyComp) macro registers the class with the factory.\n\n"
            "Debug: factory.print() lists all registered types and active overrides. "
            "Essential for understanding what's actually being instantiated."
        ),
    },
    {
        "id": 11, "topic": "UVM", "skill": "UVM", "difficulty": "C",
        "question": "What is TLM (Transaction Level Modeling) in UVM? Explain ports, exports, and analysis ports.",
        "answer": (
            "TLM decouples producers and consumers via standardized port interfaces — "
            "components talk through transactions, not signals.\n\n"
            "uvm_blocking_put_port: producer calls put(item) — blocks until consumer accepts.\n"
            "uvm_blocking_get_port: consumer calls get(item) — blocks until item is available.\n\n"
            "Ports vs Exports: a port initiates the call; an export provides the implementation. "
            "Connect port to export in connect_phase. Ports cannot connect to ports directly.\n\n"
            "uvm_analysis_port: broadcast — one writer, many listeners. "
            "Call .write(item), all connected analysis_exports receive it simultaneously. "
            "Used by monitors to broadcast observed transactions to scoreboards, coverage collectors, etc.\n\n"
            "uvm_tlm_fifo: a FIFO that implements both put and get ports — bridges "
            "producer/consumer timing differences.\n\n"
            "Key rule: connect() in connect_phase, direction goes port.connect(export)."
        ),
    },
    # ── Formal ────────────────────────────────────────────────────────────────
    {
        "id": 12, "topic": "Formal", "skill": "Formal", "difficulty": "C",
        "question": "Explain formal verification vs simulation. What are assumptions, assertions, and cover in formal?",
        "answer": (
            "Formal verification mathematically PROVES properties hold for ALL possible inputs "
            "and all reachable states — not just the inputs your testbench generated.\n\n"
            "Simulation: finite number of vectors, finite coverage. Can find bugs but cannot "
            "prove absence of bugs (only statistical confidence).\n\n"
            "In formal (using assume/assert/cover):\n"
            "assume property(p): constrains the input space. Tells the formal tool to only "
            "consider scenarios where p holds. Equivalent to 'the environment guarantees this'.\n\n"
            "assert property(p): what YOU are trying to prove. The tool tries to find a "
            "counterexample (CEX) that violates p. If none found within the bound — it's proven.\n\n"
            "cover property(p): asks 'can p ever be true?' — reachability check. "
            "Use to verify your assumptions are not over-constraining.\n\n"
            "Bounded Model Checking (BMC): searches up to depth N cycles for a CEX. "
            "Full proof requires k-induction or induction-based techniques."
        ),
    },
    {
        "id": 13, "topic": "Formal", "skill": "Formal", "difficulty": "B",
        "question": "What is a vacuous assertion? How do you detect and fix it?",
        "answer": (
            "A vacuous assertion is one that is TRIVIALLY true because its antecedent (trigger "
            "condition) can never be satisfied — it never fires, so it's never violated.\n\n"
            "Example: assert property(@(posedge clk) (state == SEND_DATA) |-> payload_valid);\n"
            "If SEND_DATA is never reached (e.g., due to an over-constrained assume), the "
            "assertion vacuously passes — zero useful checking.\n\n"
            "Detection:\n"
            "1. Run coverage: cover property(@(posedge clk) (state == SEND_DATA)) — if 0 hits, "
            "the antecedent is unreachable.\n"
            "2. Formal tools report 'vacuous proof' — treat this as a warning.\n\n"
            "Fix:\n"
            "1. Check assume blocks — are you over-constraining inputs?\n"
            "2. Add cover statements for the trigger to verify reachability.\n"
            "3. Use 'strong(seq)' to require the sequence to complete at least once.\n\n"
            "Rule: every assert should have a matching cover with the same trigger."
        ),
    },
    # ── CDC ────────────────────────────────────────────────────────────────────
    {
        "id": 14, "topic": "CDC", "skill": "CDC", "difficulty": "D",
        "question": "What is Clock Domain Crossing (CDC)? Explain metastability and the 2-flop synchronizer.",
        "answer": (
            "CDC: a signal transitions from logic clocked by domain A to logic clocked by domain B. "
            "If the domains are asynchronous (no fixed phase relationship), setup/hold violations "
            "can occur — leading to metastability.\n\n"
            "Metastability: a flip-flop output oscillates at an indeterminate voltage between 0 and 1 "
            "for some time (resolution time). It WILL resolve — but there's a probability it takes "
            "longer than one clock period, causing the next flop to capture a wrong value.\n\n"
            "2-Flop Synchronizer: the standard fix for single-bit CDC signals.\n"
            "D → FF1 (destination clock) → FF2 (destination clock) → output\n"
            "FF1 may go metastable, but has a full clock period to resolve before FF2 samples it. "
            "MTBF (Mean Time Between Failures) improves exponentially with each added stage.\n\n"
            "Limitations: ONLY safe for single-bit or gray-coded multi-bit signals. "
            "For multi-bit data: use async FIFOs with gray-coded pointers, or handshake protocols."
        ),
    },
    {
        "id": 15, "topic": "CDC", "skill": "CDC", "difficulty": "C",
        "question": "How does an asynchronous FIFO work? Explain the gray-code pointer technique.",
        "answer": (
            "Async FIFO: separate write clock (wr_clk) and read clock (rd_clk). "
            "Write pointer increments in wr_clk domain; read pointer in rd_clk domain. "
            "FULL/EMPTY flags require comparing pointers across domains — a CDC problem.\n\n"
            "Problem: binary counters have multiple bits changing simultaneously. "
            "Synchronizing a multi-bit counter can cause multiple metastability events — "
            "you might read a partially-transitioned value.\n\n"
            "Gray Code solution: only ONE bit changes per increment. "
            "Convert binary pointer to gray before synchronizing. Synchronize the gray pointer "
            "across the domain. Convert back to binary for address decoding.\n\n"
            "FULL detection: wr_ptr_gray == {~rd_ptr_gray[N:N-1], rd_ptr_gray[N-2:0]} "
            "(MSB and MSB-1 are inverted — pointers have wrapped around each other).\n\n"
            "EMPTY detection: rd_ptr_gray == synchronized wr_ptr_gray (pointers are equal).\n\n"
            "Key: compare gray pointers in the appropriate domain — rd_ptr compared in wr domain for FULL."
        ),
    },
    # ── Testplan ──────────────────────────────────────────────────────────────
    {
        "id": 16, "topic": "Testplan", "skill": "Testplan", "difficulty": "D",
        "question": "How do you write a DV testplan? What are the key components?",
        "answer": (
            "A testplan maps design specification features to verification scenarios.\n\n"
            "Key components:\n"
            "1. Feature list: extract every feature from the spec. 'AHB slave must assert HREADY "
            "within 4 cycles of HSEL' → one testplan entry.\n\n"
            "2. For each feature: test name, stimulus description, checking method (assertion, "
            "scoreboard, explicit check), pass/fail criteria, coverage closure requirement.\n\n"
            "3. Priority/risk: P0 = must pass before tapeout, P1 = important, P2 = nice-to-have.\n\n"
            "4. Coverage closure plan: which covergroups close the feature? What bins must hit?\n\n"
            "5. Corner cases: reset during transaction, back-to-back transfers, max payload, "
            "address boundary conditions, error injection, interrupt during operation.\n\n"
            "Format: often a spreadsheet or structured YAML/JSON that can be parsed to auto-generate "
            "test skeletons. Some teams use tools like VManager or Mentor Questa Verification Academy.\n\n"
            "Review: testplan should be reviewed against spec by designer AND verification lead."
        ),
    },
    {
        "id": 17, "topic": "Testplan", "skill": "Testplan", "difficulty": "C",
        "question": "Explain regression testing in DV — what is it, how do you manage it, and what metrics matter?",
        "answer": (
            "Regression: running the full test suite regularly (nightly) to catch regressions "
            "from new RTL or testbench changes.\n\n"
            "Structure:\n"
            "- Sanity regression: ~10 tests, must pass before code check-in. Fast (~1 hour).\n"
            "- Nightly regression: full suite, 100–10,000 tests with different seeds. Run overnight.\n"
            "- Pre-tapeout regression: extended run with increased seeds and corner cases.\n\n"
            "Metrics that matter:\n"
            "1. Pass rate: % of tests that pass. Target 100% (with known waived failures tracked).\n"
            "2. Code coverage: line, branch, toggle, FSM. Tool-generated, easier to close.\n"
            "3. Functional coverage: user-defined, spec-based. Harder to close — shows verification quality.\n"
            "4. Assertion coverage: % of properties that fired at least once (non-vacuous).\n\n"
            "Seed management: fixed seeds for reproducibility; random seeds for exploration. "
            "Track failing seeds for debug.\n\n"
            "CI/CD: integrate with Jenkins/GitLab CI. Block merges if sanity regression fails."
        ),
    },
    # ── Protocols ──────────────────────────────────────────────────────────────
    {
        "id": 18, "topic": "Protocols", "skill": "Testplan", "difficulty": "D",
        "question": "Describe the APB (Advanced Peripheral Bus) protocol. What are the key signals and phases?",
        "answer": (
            "APB (AMBA APB v2) is a simple, low-bandwidth peripheral bus.\n\n"
            "Key signals:\n"
            "PCLK, PRESETn (active-low reset)\n"
            "PADDR[31:0]: address\n"
            "PWDATA[31:0], PRDATA[31:0]: write/read data\n"
            "PWRITE: 1=write, 0=read\n"
            "PSEL: slave select\n"
            "PENABLE: second phase enable\n"
            "PREADY: slave extends transfer (wait states)\n"
            "PSLVERR: slave error response\n\n"
            "Two-phase transfer:\n"
            "SETUP phase: PSEL=1, PADDR/PWDATA/PWRITE set. PENABLE=0.\n"
            "ACCESS phase: PENABLE=1. Transfer completes when PREADY=1. "
            "If PREADY=0, slave inserts wait states.\n\n"
            "No burst mode. One transfer per two+ cycles. Simple to verify: "
            "assert no PENABLE without preceding PSEL. Assert PREADY deasserts within timeout. "
            "Check PSLVERR handling in the master."
        ),
    },
    {
        "id": 19, "topic": "Protocols", "skill": "CDC", "difficulty": "C",
        "question": "Compare AHB and APB protocols. When would you use each?",
        "answer": (
            "AHB (Advanced High-performance Bus): pipelined, high bandwidth.\n"
            "- Pipelined: address phase of next transfer overlaps data phase of current.\n"
            "- Burst transfers: INCR4, INCR8, WRAP4 etc. — multiple beats in one address phase.\n"
            "- Multi-master: arbiter selects who drives the bus (HGRANT).\n"
            "- Signals: HADDR, HWDATA, HRDATA, HWRITE, HSIZE, HBURST, HTRANS (IDLE/BUSY/NONSEQ/SEQ), HREADY.\n"
            "- Pipelining: decode HADDR in cycle N, capture HWDATA in cycle N+1.\n\n"
            "APB: simple, low bandwidth.\n"
            "- No pipelining, no burst, no multi-master.\n"
            "- Two-phase: SETUP then ACCESS.\n"
            "- Lower power, smaller area — ideal for slow peripherals (UART, timers, GPIO).\n\n"
            "System architecture: CPU → AHB (cache, DMA, memory controllers) → AHB-to-APB bridge → APB peripherals.\n\n"
            "Verify AHB: check HTRANS transitions (no SEQ after IDLE without NONSEQ first), "
            "HREADY propagation, burst termination."
        ),
    },
    # ── Python / Scripting ─────────────────────────────────────────────────────
    {
        "id": 20, "topic": "Python", "skill": "Python", "difficulty": "E",
        "question": "How is Python used in DV/EDA workflows? Name 3 specific use cases.",
        "answer": (
            "Python is the scripting backbone of modern DV flows:\n\n"
            "1. Testplan parsing and test generation: parse YAML/Excel testplans, auto-generate "
            "UVM test skeletons, seed lists, and regression scripts. Reduces manual work.\n\n"
            "2. Waveform/log parsing: parse simulation logs (UVM report, regression CSV), "
            "extract coverage numbers, flag failures, generate dashboards. Used with re/pandas.\n\n"
            "3. EDA tool scripting: Synopsys VCS, Cadence Xcelium, Mentor Questa all have "
            "Python APIs. Automate compilation, simulation, and coverage merge. "
            "cocotb: Python-based testbench framework — write UVM-like tests in pure Python.\n\n"
            "4. Register model generation: parse IP-XACT or custom spec → generate UVM RAL "
            "(Register Abstraction Layer) models automatically. Tools like PeakRDL.\n\n"
            "5. Coverage analysis: merge ucdb/vdb files, compute closure, generate HTML reports. "
            "Script-based triage of which features are uncovered.\n\n"
            "Key libraries: re, subprocess, pandas, yaml, jinja2 (for template generation)."
        ),
    },
    {
        "id": 21, "topic": "Python", "skill": "Python", "difficulty": "D",
        "question": "Explain Python generators and how they can model streaming protocol stimulus.",
        "answer": (
            "A generator is a function that yields values lazily — it produces one item at a time "
            "rather than building an entire list. State is preserved between yields.\n\n"
            "def packet_gen(count):\n"
            "    for i in range(count):\n"
            "        payload = random.randbytes(64)\n"
            "        yield {'id': i, 'data': payload, 'last': i == count-1}\n\n"
            "In cocotb (Python testbench), this models streaming stimulus perfectly:\n"
            "async for pkt in packet_gen(1000):\n"
            "    await driver.send(pkt)  # drive one packet, wait for handshake\n\n"
            "Benefits for DV:\n"
            "- Infinite sequences without memory: generate transactions on demand.\n"
            "- Composable: chain generators with itertools.chain, itertools.islice.\n"
            "- Easy coverage closure: parameterize the generator to hit specific bins.\n\n"
            "Python's async/await + generators work naturally with cocotb's coroutine model, "
            "which mirrors UVM sequence/driver interaction."
        ),
    },
    # ── Architecture / Mixed ────────────────────────────────────────────────────
    {
        "id": 22, "topic": "Architecture", "skill": "Testplan", "difficulty": "C",
        "question": "Explain the UVM RAL (Register Abstraction Layer). Why is it important?",
        "answer": (
            "RAL provides a standardized, abstract representation of a DUT's register map. "
            "Instead of driving raw bus signals, tests read/write named register fields.\n\n"
            "Key classes:\n"
            "uvm_reg_block: top-level container for the register map.\n"
            "uvm_reg: one register with named fields (uvm_reg_field).\n"
            "uvm_reg_map: maps registers to addresses on a specific bus interface.\n\n"
            "Operations:\n"
            "reg.write(status, 32'hDEAD_BEEF, .parent(this)): drives the bus, waits for response.\n"
            "reg.read(status, rdata, .parent(this)): reads via bus.\n"
            "reg.get()/set(): access mirror (predicted) value without bus access.\n"
            "reg.predict(): update mirror manually.\n\n"
            "Built-in tests: uvm_reg_hw_reset_seq (checks reset values), "
            "uvm_reg_bit_bash_seq (walks 1s and 0s), uvm_reg_access_seq (read-write checks).\n\n"
            "Benefits: portable (swap bus adapter to reuse on APB vs AHB), auto-generated "
            "from IP-XACT specs, self-checking with mirror comparison."
        ),
    },
    {
        "id": 23, "topic": "Architecture", "skill": "Formal", "difficulty": "B",
        "question": "What is k-induction in formal verification? How does it extend BMC?",
        "answer": (
            "BMC (Bounded Model Checking): tries to find a counterexample within K cycles. "
            "If none found up to K, property is 'safe' up to K — but NOT proven for all depths.\n\n"
            "k-induction proves properties for ALL depths in two steps:\n\n"
            "Base case: prove the property holds for k consecutive cycles starting from reset "
            "(same as BMC depth k).\n\n"
            "Inductive step: ASSUME the property holds for k consecutive cycles (the inductive "
            "hypothesis). PROVE it holds at cycle k+1. If true, by induction it holds forever.\n\n"
            "Problem: the inductive hypothesis must be over REACHABLE states. If the inductive "
            "step fails, it's often because the tool finds an unreachable state where the "
            "property breaks.\n\n"
            "Solutions:\n"
            "1. Strengthen the property (add invariants as additional assumes).\n"
            "2. Increase k — more context makes the inductive step easier.\n"
            "3. Use auxiliary invariants discovered by tools (IC3/PDR algorithm).\n\n"
            "IC3/PDR (Property Directed Reachability): modern formal engines iteratively build "
            "inductive invariants — often converges much faster than naive k-induction."
        ),
    },
    {
        "id": 24, "topic": "Architecture", "skill": "CDC", "difficulty": "B",
        "question": "Explain a handshake-based CDC scheme and when to use it instead of a 2-flop synchronizer.",
        "answer": (
            "2-flop synchronizer limitations: safe ONLY for single-bit control signals "
            "(req/ack, enable) or gray-coded pointers. NOT safe for multi-bit data buses.\n\n"
            "Handshake (req-ack) scheme:\n"
            "1. Sender (domain A): assert req, put data on bus, hold stable.\n"
            "2. Synchronize req into domain B (2-flop sync).\n"
            "3. Receiver (domain B): capture data, assert ack.\n"
            "4. Synchronize ack back into domain A (2-flop sync).\n"
            "5. Sender deasserts req after seeing ack.\n"
            "6. Receiver deasserts ack after seeing req deasserted.\n\n"
            "Data is guaranteed stable during steps 2-3, so no metastability on multi-bit data.\n\n"
            "When to use:\n"
            "- Multi-bit control words that cannot be gray-coded.\n"
            "- Low-frequency transfers where latency (~4-6 cycles per direction) is acceptable.\n\n"
            "When NOT to use:\n"
            "- High-bandwidth data streams — use async FIFO instead.\n\n"
            "Formal verification of CDC: tools like Synopsys VC SpyGlass CDC check for "
            "unsynchronized paths, reconvergence (multiple synchronized copies of same source), "
            "and data stability requirements."
        ),
    },
    {
        "id": 25, "topic": "Architecture", "skill": "Assertions", "difficulty": "B",
        "question": "How do you verify a finite state machine (FSM) using SVA and formal?",
        "answer": (
            "Step 1 — Enumerate all states and transitions from the spec:\n"
            "Draw the state diagram. Each arc becomes a property.\n\n"
            "Step 2 — Write SVA properties:\n"
            "// State transition: IDLE → SEND only when valid && ready\n"
            "property idle_to_send;\n"
            "  @(posedge clk) (state == IDLE && valid && ready) |=> (state == SEND);\n"
            "endproperty\n\n"
            "// Illegal state: must never be in UNDEFINED state\n"
            "property no_illegal_state;\n"
            "  @(posedge clk) state inside {IDLE, SEND, RECEIVE, ERROR};\n"
            "endproperty\n\n"
            "Step 3 — Cover all states and transitions:\n"
            "cover property (@(posedge clk) (state == SEND)) — ensure SEND is reachable.\n\n"
            "Step 4 — Formal verification:\n"
            "assert all transition properties + no-illegal-state. Formal proves them or gives a CEX.\n"
            "Advantage: formal explores ALL input combinations, finds transition bugs "
            "that random simulation would rarely hit (e.g., glitch on reset during SEND state).\n\n"
            "Step 5 — Check reset recovery:\n"
            "property reset_recovery;\n"
            "  @(posedge clk) !rst_n |=> (state == IDLE);\n"
            "endproperty"
        ),
    },
]
