import networkx as nx
import numpy as np
import optparse
import sys

def print_usage(option, opt, value, parser):
    usage_message = """
    This program will calculate the network-based distance d_AB and
    separation s_AB between two gene sets A and B.
    
    * Required input:
    
      two files containing the gene sets A and B. The file must be in form
      of a table, one gene per line. If the table contains several
      columns, they must be tab-separated, only the first column will be
      used. See the two files MS.txt and PD.txt for valid examples (they
      contain genes for multiple sclerosis and peroxisomal disorders,
      respectively).
    
    * Optional input:  
    
      - file containing an interaction network. If now file is given, the
        default network \"interactome.tsv\" will be used instead. The file
        must contain an edgelist provided as a tab-separated table. The
        first two columns of the table will be interpreted as an
        interaction gene1 <==> gene2
    
     - filename for the output. If none is given,
       \"separation_results.txt\" will be used
     
    
    Here's an example that should work, provided the files are in the same
    directory as this python script:
    
    ./separation.py -n interactome.tsv --g1 MS.txt --g2 PD.txt -o output.txt
    
    
    
        """
    
    print (usage_message)
    sys.exit()
    

def read_network(network_file):
    """
    Reads a network from an external file.

    * The edgelist must be provided as a tab-separated table. The
    first two columns of the table will be interpreted as an
    interaction gene1 <==> gene2

    * Lines that start with '#' will be ignored
    """

    G = nx.Graph()
    for line in open(network_file,'r'):
        # lines starting with '#' will be ignored
        if line[0]=='#':
            continue
        # The first two columns in the line will be interpreted as an
        # interaction gene1 <=> gene2
        line_data   = line.strip('\n').split('\t')
        if len(line_data) < 2:
            continue
        node1 = line_data[0]
        node2 = line_data[1]
        G.add_edge(node1,node2)

    print ("\n> done loading network:")
    print ("> network contains %s nodes and %s links" %(G.number_of_nodes(),
                                                       G.number_of_edges()))
    
    return G



def remove_self_links(G):
	#sl = G.selfloop_edges()
	sl=nx.selfloop_edges(G, data=True) 
	G.remove_edges_from(sl)


def read_gene_list(gene_file):
    """
    Reads a list genes from an external file.

    * The genes must be provided as a table. If the table has more
    than one column, they must be tab-separated. The first column will
    be used only.

    * Lines that start with '#' will be ignored
    """

    genes_set = set()
    for line in open(gene_file,'r'):
        # lines starting with '#' will be ignored
        if line[0]=='#':
            continue
        # the first column in the line will be interpreted as a seed
        # gene:
        line_data = line.strip('\n').split('\t')
        gene      = line_data[0]
        genes_set.add(gene)

    print ("\n> done reading genes:")
    #print ("> %s genes found in %s") %(len(genes_set),gene_file)

    return genes_set



def get_pathlengths_for_two_sets(G,given_gene_set1,given_gene_set2):
    
    """
    calculate the shortest paths between two given set of genes in a
    given network. The results are stored in a dictionary of
    dictionaries: all_path_lenghts[gene1][gene2] = l with gene1 <
    gene2, so each pair is stored only once!

    PARAMETERS:
    -----------
        - G: network
        - gene_set1/2: gene sets for which paths should be computed

    RETURNS:
    --------
        - all_path_lenghts[gene1][gene2] = l for all pairs of genes
          with gene1 < gene2

    """ 

    # remove all nodes that are not in the network
    all_genes_in_network = set(G.nodes())
    gene_set1 = given_gene_set1 & all_genes_in_network
    gene_set2 = given_gene_set2 & all_genes_in_network

    all_path_lenghts = {}
    
    # calculate the distance of all possible pairs
    for gene1 in gene_set1:
        if gene1 not in all_path_lenghts:
            all_path_lenghts[gene1] = {}
        for gene2 in gene_set2:
            if gene1 != gene2:
                try:
                    l = nx.shortest_path_length(G, source=gene1, target=gene2)
                    if gene1 < gene2:
                        all_path_lenghts[gene1][gene2] = l
                    else:
                        if gene2 not in all_path_lenghts:
                            all_path_lenghts[gene2] = {}
                        all_path_lenghts[gene2][gene1] = l
                except:
                    continue

    return all_path_lenghts

def calc_set_pair_distances(G,given_gene_set1,given_gene_set2):

    """
    Calculates the mean shortest distance between two sets of genes on
    a given network
    
    PARAMETERS:
    -----------
        - G: network
        - gene_set1/2: gene sets for which distance will be computed 

    RETURNS:
    --------
         - mean shortest distance 

    """

    # remove all nodes that are not in the network
    all_genes_in_network = set(G.nodes())
    gene_set1 = given_gene_set1 & all_genes_in_network
    gene_set2 = given_gene_set2 & all_genes_in_network

    # get the network distances for all gene pairs:
    all_path_lenghts = get_pathlengths_for_two_sets(G,gene_set1,gene_set2)

    all_distances = []

    # going through all pairs starting from set 1 
    for geneA in gene_set1:

        all_distances_A = []
        for geneB in gene_set2:

            # the genes are the same, so their distance is 0
            if geneA == geneB:
                all_distances_A.append(0)
                
            # I have to check which gene is 'smaller' in order to know
            # where to look up the distance of that pair in the
            # all_path_lengths dict
            else:
                if geneA < geneB:
                    try:
                        all_distances_A.append(all_path_lenghts[geneA][geneB])
                    except:
                        pass
                        
                else:
                    try:
                        all_distances_A.append(all_path_lenghts[geneB][geneA])
                    except:
                        pass


        if len(all_distances_A) > 0:
            l_min = min(all_distances_A)
            all_distances.append(l_min)


    # going through all pairs starting from disease B
    for geneA in gene_set2:

        all_distances_A = []
        for geneB in gene_set1:

            # the genes are the same, so their distance is 0
            if geneA == geneB:
                all_distances_A.append(0)

            # I have to check which gene is 'smaller' in order to know
            # where to look up the distance of that pair in the
            # all_path_lengths dict
            else:
                if geneA < geneB:
                    try:
                        all_distances_A.append(all_path_lenghts[geneA][geneB])
                    except:
                        pass
                        
                else:
                    try:
                        all_distances_A.append(all_path_lenghts[geneB][geneA])
                    except:
                        pass


        if len(all_distances_A) > 0:
            l_min = min(all_distances_A)
            all_distances.append(l_min)

    # calculate mean shortest distance
    mean_shortest_distance = np.mean(all_distances)

    return mean_shortest_distance


def get_pathlengths_for_single_set(G,given_gene_set):
    
    """
    calculate the shortest paths of a given set of genes in a
    given network. The results are stored in a dictionary of
    dictionaries:
    all_path_lengths[gene1][gene2] = l
    with gene1 < gene2, so each pair is stored only once!

    PARAMETERS:
    -----------
        - G: network
        - gene_set: gene set for which paths should be computed

    RETURNS:
    --------
        - all_path_lenghts[gene1][gene2] = l for all pairs of genes
          with gene1 < gene2

    """ 

    # remove all nodes that are not in the network
    all_genes_in_network = set(G.nodes())
    gene_set = given_gene_set & all_genes_in_network

    all_path_lenghts = {}
    
    # calculate the distance of all possible pairs
    for gene1 in gene_set:
        if gene1 not in all_path_lenghts:
            all_path_lenghts[gene1] = {}
        for gene2 in gene_set:
            if gene1 < gene2:
                try:
                    l = nx.shortest_path_length(G, source=gene1, target=gene2)
                    all_path_lenghts[gene1][gene2] = l
                except:
                    continue

    return all_path_lenghts


def calc_single_set_distance(G,given_gene_set):

    """
    Calculates the mean shortest distance for a set of genes on a
    given network    
    

    PARAMETERS:
    -----------
        - G: network
        - gene_set: gene set for which distance will be computed 

    RETURNS:
    --------
         - mean shortest distance 

    """


    # remove all nodes that are not in the network, just to be safe
    all_genes_in_network = set(G.nodes())
    gene_set = given_gene_set & all_genes_in_network

    # get the network distances for all gene pairs:
    all_path_lenghts = get_pathlengths_for_single_set(G,gene_set)

    all_distances = []

    # going through all gene pairs
    for geneA in gene_set:

        all_distances_A = []
        for geneB in gene_set:

            # I have to check which gene is 'smaller' in order to know
            # where to look up the distance of that pair in the
            # all_path_lengths dict
            if geneA < geneB:
                if geneB in all_path_lenghts[geneA]:
                    all_distances_A.append(all_path_lenghts[geneA][geneB])
            else:
                if geneA in all_path_lenghts[geneB]:
                    all_distances_A.append(all_path_lenghts[geneB][geneA])

        if len(all_distances_A) > 0:
            l_min = min(all_distances_A)
            all_distances.append(l_min)

    # calculate mean shortest distance
    mean_shortest_distance = np.mean(all_distances)

    return mean_shortest_distance



G  = read_network("interaction.tsv")
all_genes_in_network = set(G.nodes())
remove_self_links(G)
genes_A_full = read_gene_list("celiac disease.txt")
genes_A = genes_A_full & all_genes_in_network
genes_B_full = read_gene_list("cerebellar ataxia.txt")
genes_B = genes_B_full & all_genes_in_network
d_A = calc_single_set_distance(G,genes_A)
d_B = calc_single_set_distance(G,genes_B)
d_AB = calc_set_pair_distances(G,genes_A,genes_B)
s_AB = d_AB - (d_A + d_B)/2
results_message = """
> gene set A from \"%s\": %s genes
> network-diameter: d_A = %s
> gene set B from \"%s\": %s genes
> network-diameter: d_B = %s
> mean shortest distance between A & B: d_AB = %s 
> network separation of A & B: s_AB = %s
"""%("MS_3.txt",len(genes_A),d_A,
     "RA_3.txt",len(genes_B),d_B,
     d_AB,s_AB)
print (results_message)
fp = open("results_file_new_100_genes.txt",'w')
fp.write(results_message)
fp.close()

    #print ("> results have been saved to %s") % (results_file)





