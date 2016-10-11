import pandas
import time
import os
import sys
import urllib2
from lxml import html
import operator
import paths
import matplotlib.pylab as plt
import seaborn as sns

def get_patent_page(patent_id):
    url = "https://patents.google.com/patent/%s/en" %(patent_id)
    print "Fetching %s" %(url)
    page = None
    try:
        page = urllib2.urlopen(url).read()
    except urllib2.HTTPError as e:
        print "HTML error: ", e
    return page

def get_patent_info(page):
    """
    Get patent information from page.
    """
    tree = html.fromstring(page)
    # get current assignee
    info = {}
    info["assigneeOriginal"] = \
      ",".join(tree.xpath('//dd[@itemprop="assigneeOriginal"]/text()'))
    info["inventor"] = \
      ",".join(tree.xpath('//dd[@itemprop="inventor"]/text()'))
    info["priorityDate"] = ",".join(tree.xpath('//dd/time[@itemprop="priorityDate"]/text()'))
    info["filingDate"] = ",".join(tree.xpath('//dd/time[@itemprop="filingDate"]/text()'))
    info["publicationDate"] = ",".join(tree.xpath('//dd/time[@itemprop="publicationDate"]/text()'))
    info["grantDate"] = ",".join(tree.xpath('//dd/time[@itemprop="grantDate"]/text()'))    
    return info

def process_patents(input_fname, output_fname):
    # roughly 20k out 30k are US patents
    if os.path.isfile(output_fname):
        print "Output file exists, quitting."
        return 
    data = pandas.read_table(f, sep=",")
    # select only US patents
    data = data[data["Country"] == "US"]

    entries = []
    t1 = time.time()
    out_file = open(output_fname, "w")
    columns = ["patent_id", "patent_title", "assigneeOriginal", "filingDate",
               "publicationDate", "grantDate"]
    out_file.write("\t".join(columns) + "\n")
    num_skipped = 0
    for patent_id, patent_title in zip(data["Reference"], data["Title"]):
        page = get_patent_page(patent_id)
        if page is None: continue
        patent_info = get_patent_info(page)
        entry = {"patent_id": patent_id,
                 "patent_title": patent_title}
        entry.update(patent_info)
        values = [entry[col] for col in columns]
        line = "\t".join(values) + "\n"
        try:
            line = line.encode("utf-8")
        except UnicodeDecodeError:
            print "Skipping: %s" %(line)
            num_skipped += 1
            continue
        print line.strip()
        out_file.write(line)
    out_file.close()
    t2 = time.time()
    print "patent parsing took %.2f minutes" %((t2 - t1)/60.)
    print "Skipped total of %d lines" %(num_skipped)

def get_university_patents(patents):
    # drop any patents without original assignee information
    patents = patents.dropna(subset=["assigneeOriginal"])
    # exclude non-US universities that are registered as US patents
    # exclude Tel Aviv University
    patents = patents[~patents["assigneeOriginal"].str.contains("Tel Aviv")]
    # exclude Hebrew University
    patents = patents[~patents["assigneeOriginal"].str.contains("Hebrew University")]
    # exclude Singapore 
    patents = patents[~patents["assigneeOriginal"].str.contains("Singapore")]
    # exclude Hong Kong
    patents = patents[~patents["assigneeOriginal"].str.contains("Hong Kong")]
    # exclude Pohang
    patents = patents[~patents["assigneeOriginal"].str.contains("Pohang University")]
    # exclude Tohoku University
    patents = patents[~patents["assigneeOriginal"].str.contains("Tohoku University")]
    # exclude Hiroshima University
    patents = patents[~patents["assigneeOriginal"].str.contains("Hiroshima University")]
    # universities regular expression
    univ_pattern = \
      "University|California Institute of Technology|New Jersey Institute of Technology"
    univ_patents = patents[patents["assigneeOriginal"].str.contains(univ_pattern)]
    return univ_patents

def get_stats(patents):
    names = ["Linus Torvalds",
             "US Secretary of Navy",
             "Elwha LLC",
             "Raytheon",
             "Lockheed Martin"]
    num_total = len(patents)
    print "getting statistics for %d patents" %(num_total)
    for name in names:
        results = patents[patents["assigneeOriginal"].str.contains(name)]
        num_results = len(results)
        print "%d from %s" %(num_results, name)

def main():
    input_fname = \
      os.path.join(paths.DATA_DIR, "ivpatents_sept23_2016.csv")
    output_fname = \
      os.path.join(paths.DATA_DIR,
                   "ivpatents_sept23_2016.info.with_dates.txt")
    # get patents information
    process_patents(input_fname, output_fname)
    # load all patents
    patents = pandas.read_table(output_fname, sep="\t")
    # load university patents
    num_total = len(patents)
    patents = patents.dropna(subset=["assigneeOriginal"])
    num_assignee = len(patents)
    print "%d/%d patents have original assignee" %(num_assignee,
                                                   num_total)
    # get statistics on patents
    get_stats(patents)
    # do university patents analysis
    univ_patents = get_university_patents(patents)
    print "total of %d university patents" %(len(univ_patents))
    # output university patents to file
    univ_patents_fname = os.path.join(paths.DATA_DIR, "ivpatents_universities.txt")
    print "writing university patents to: %s" %(univ_patents_fname)
    univ_patents.to_csv(univ_patents_fname, sep="\t", index=False,
                        cols=["patent_id", "patent_title", "assigneeOriginal",
                              "filingDate", "publicationDate", "grantDate"])
    # summarize the top schools
    univ_summary = univ_patents.groupby("assigneeOriginal").groups
    for univ in univ_summary:
        univ_summary[univ] = len(univ_summary[univ])
    sorted_univ_summary = sorted(univ_summary.items(),
                                 key=operator.itemgetter(1),
                                 reverse=True)
    univ_df = []
    for univ, num_patents in sorted_univ_summary:
        entry = {"University": univ,
                 "num_patents": num_patents}
        univ_df.append(entry)
    univ_df = pandas.DataFrame(univ_df)
    # abbreviate
    univ_df["University"] = \
      univ_df["University"].str.replace("New York", "NY")
    univ_df["University"] = \
      univ_df["University"].str.replace("Institute", "Inst.")
    univ_df["University"] = \
      univ_df["University"].str.replace("California", "Cal.")
    univ_df["University"] = \
      univ_df["University"].str.replace("Polytechnic", "Polytech.")
    univ_df["University"] = \
      univ_df["University"].str.replace("University", "Univ.")
    univ_df["University"] = \
      univ_df["University"].str.replace("Technology", "Tech.")
    univ_df["University"] = \
      univ_df["University"].str.replace("Research Foundation of", "")
    univ_df["University"] = \
      univ_df["University"].str.replace("New Jersey", "NJ")
    print univ_df.head()
    print " -- "
    top_n = 10
    univ_df = univ_df[0:top_n]
    plt.figure(figsize=(5.5, 3.5))
    plot_fname = os.path.join(paths.PLOTS_DIR, "ivpatents_univ.pdf")
    #sns.countplot(y="num_patents", data=univ_df)
    sns.set_style("ticks")
    #univ_df.plot(x="University", kind="bar")
    x_axis = range(len(univ_df["University"]))
    g = sns.barplot(x="University", y="num_patents", data=univ_df, color="k")
    g.set_xticklabels(g.get_xticklabels(), rotation=55, ha="right")
    plt.ylabel("Number of IV patents")
    plt.xlabel("Original patent assignee")
    plt.tight_layout()
    sns.despine(trim=True)
    plt.tight_layout()
    plt.savefig(plot_fname)

if __name__ == "__main__":
    main()


    

