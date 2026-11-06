# Third-party data and notices

## Sentiment Labelled Sentences

The files in `examples/uci_sentiment/data/`, text and labels derived from them in `examples/uci_sentiment/results/`, derived model-experiment inputs in `examples/uci_sentiment/model_experiment/results/`, and source text shown in the case study/report are derived from:

Kotzias, D. (2015). **Sentiment Labelled Sentences** [Dataset]. UCI Machine Learning Repository. https://doi.org/10.24432/C57604

Dataset landing page: https://archive.ics.uci.edu/dataset/331/sentiment+labelled+sentences

UCI lists the dataset under the **Creative Commons Attribution 4.0 International license**: https://creativecommons.org/licenses/by/4.0/

The source dataset contains sentences from Amazon, IMDb and Yelp. Related paper: Dimitrios Kotzias, Misha Denil, Nando de Freitas and Padhraic Smyth, *From Group to Individual Labels Using Deep Features*, KDD 2015.

Original selected text-file bytes are unchanged. We parse their labels and text, add source-file/line identifiers, create explicitly documented source-domain, row-random and component-based partitions, and generate audit reports and figures. These adaptations do not imply endorsement by the creators, the websites or UCI. The underlying dataset text/labels remain subject to their own license; the software MIT license does not relicense the source data. Retrieval date and hashes are in the case study's source manifest.

The repository's synthetic example is separately labeled and is not drawn from this corpus.

## Browser runtime

The browser app fetches unmodified Pyodide 0.29.3 assets from its versioned jsDelivr distribution. Pyodide uses MPL-2.0: https://github.com/pyodide/pyodide/blob/main/LICENSE . Runtime binaries are not vendored or relicensed here. The generated HTML embeds UCI demonstration records; their CC BY 4.0 notice above still applies.
