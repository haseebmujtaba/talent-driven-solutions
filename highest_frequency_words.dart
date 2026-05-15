// 22k-4307
// Haseeb Mujtaba

void main() {
  List<String> sentences = [
    "this is a test this is",
    "hello hello world",
    "dart is fun fun fun"
  ];

  print("The following words have the highest word frequency per line:");

  for (int i = 0; i < sentences.length; i++) {
    List<String> highFreqWords = getHighestFrequencyWords(sentences[i]);
    print("$highFreqWords (appears in line ${i + 1})");
  }
}

List<String> getHighestFrequencyWords(String sentence) {
  List<String> words = sentence.toLowerCase().split(RegExp(r'\s+'));

  Map<String, int> frequency = {};
  for (String word in words) {
    if (word.isNotEmpty) {
      frequency[word] = (frequency[word] ?? 0) + 1;
    }
  }

  int maxFreq = frequency.values.reduce((a, b) => a > b ? a : b);

  List<String> result = frequency.entries
      .where((entry) => entry.value == maxFreq)
      .map((entry) => entry.key)
      .toList();

  return result;
}
