# ACE

ACE (*AC state-change rule extraction procedurE*) extracts access control policies and sequences of state-change rules from BPMN workflows. ACE is usually used in combination with [ANNA](https://github.com/stfbk/ANNA) to allow measuring the performance of access control enforcement mechanisms (e.g., [OPA](https://www.openpolicyagent.org/), [XACML](http://docs.oasis-open.org/xacml/3.0/xacml-3.0-core-spec-os-en.html) and [CryptoAC](https://github.com/stfbk/CryptoAC)) through the **simulated execution of realistic workflows**.

The design of ACE was firstly described in the (yet to be published) article "*A Simulation Framework for the Experimental Evaluation of Access Control Enforcement Mechanisms based on Business Processes*".

Run the [helper](./launchHelper.sh) to get more information on ACE, or launch the [scripts](./scripts/) to run ACE on the example [workflows](./workflows/).

> **Important** - ACE is still under development; we welcome your interest and encourage you to reach out at `sberlato@fbk.eu` for more information!
